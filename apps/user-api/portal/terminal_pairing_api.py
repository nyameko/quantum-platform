"""M4g opt-in terminal pairing via existing QP identity and signed ACP proxy.

A human browser session approves a short-lived terminal proof. Only Quantum
Platform holds the ACP signer and rechecks approval/revocation for EACH call.
POSIX UID, SSH username, terminal-provided user IDs and browser cookies are
never accepted as ACP identity credentials.
"""
import hashlib
import hmac
import secrets
from datetime import timedelta
from uuid import UUID, uuid4

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from . import agent_client
from .models import TerminalPairing

PAIRING_SECONDS = 300
ACTIVE_LIMIT = 200


def _digest(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def _no_store(response):
    response["Cache-Control"] = "no-store, private"
    response["Pragma"] = "no-cache"
    return response


def _rate_limited(request, action, limit=12):
    # Defensive per-address throttle. Reverse-proxy source IP is resolved by
    # Django/ingress; do not trust spoofable X-Forwarded-For request headers.
    addr = request.META.get("REMOTE_ADDR", "unknown")[:80]
    key = "acp-pair:" + action + ":" + _digest(addr)
    count = cache.get(key, 0)
    if count >= limit:
        return True
    cache.set(key, count + 1, timeout=60)
    return False


def _pairing_proof(request):
    try:
        identity = UUID(str(request.headers.get("X-ACP-Pairing-ID", "")))
    except (ValueError, TypeError):
        return None
    header = request.headers.get("Authorization", "")
    if not header.startswith("Pairing ") or len(header) > 256:
        return None
    proof = header.removeprefix("Pairing ").strip()
    if len(proof) < 40 or len(proof) > 100 or not proof.isascii():
        return None
    return identity, _digest(proof)


def _approved_owner(request):
    proof = _pairing_proof(request)
    if proof is None:
        return None
    identity, digest = proof
    with transaction.atomic():
        pair = (
            TerminalPairing.objects.select_for_update()
            .select_related("user")
            .filter(pk=identity)
            .first()
        )
        if (
            pair is None or pair.status != TerminalPairing.Status.APPROVED
            or not pair.user_id or not pair.user.is_active
            or pair.expires_at <= timezone.now()
            or not hmac.compare_digest(pair.proof_sha256, digest)
        ):
            return None
        return pair.user


@api_view(["POST"])
@permission_classes([AllowAny])
def terminal_pair_start(request):
    """Unprivileged device-code request; it confers NO identity or ACP access."""
    if _rate_limited(request, "start", limit=10):
        return _no_store(Response({"detail": "Try pairing later."}, status=429))
    if not isinstance(request.data, dict):
        return Response({"detail": "JSON object required."}, status=400)
    label = request.data.get("device_label", "Research terminal")
    if not isinstance(label, str) or not 1 <= len(label.strip()) <= 80:
        return Response({"detail": "Device label must be 1–80 characters."}, status=400)
    if TerminalPairing.objects.filter(
        status=TerminalPairing.Status.PENDING,
        expires_at__gt=timezone.now(),
    ).count() >= ACTIVE_LIMIT:
        return _no_store(Response({"detail": "Pairing service busy."}, status=429))

    code = secrets.token_hex(6).upper()
    proof = secrets.token_urlsafe(32)
    pair = TerminalPairing.objects.create(
        id=uuid4(),
        verification_code_sha256=_digest(code),
        proof_sha256=_digest(proof),
        device_label=label.strip(),
        expires_at=timezone.now() + timedelta(seconds=PAIRING_SECONDS),
    )
    return _no_store(Response({
        "pairing_id": str(pair.id),
        "verification_code": code,
        "pairing_proof": proof,
        "verification_path": "/agent/pair/",
        "expires_in": PAIRING_SECONDS,
        "poll_interval": 3,
    }, status=201))


@api_view(["POST"])
@permission_classes([AllowAny])
def terminal_pair_status(request):
    """Only a terminal holding the unguessable proof may poll this state."""
    if not isinstance(request.data, dict):
        return _no_store(Response({"detail": "Pairing unavailable."}, status=404))
    proof = request.data.get("pairing_proof")
    try:
        pair_id = UUID(str(request.data.get("pairing_id", "")))
    except (TypeError, ValueError):
        return _no_store(Response({"detail": "Pairing unavailable."}, status=404))
    if not isinstance(proof, str) or not 40 <= len(proof) <= 100 or not proof.isascii():
        return _no_store(Response({"detail": "Pairing unavailable."}, status=404))
    pair = TerminalPairing.objects.filter(pk=pair_id).first()
    if pair is None or not hmac.compare_digest(pair.proof_sha256, _digest(proof)):
        return _no_store(Response({"detail": "Pairing unavailable."}, status=404))
    if pair.expires_at <= timezone.now() or pair.status == TerminalPairing.Status.REVOKED:
        return _no_store(Response({"state": "expired_or_revoked"}, status=410))
    return _no_store(Response({"state": pair.status}))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def terminal_pair_approve(request):
    """Human explicitly approves a displayed code in their logged-in browser."""
    if _rate_limited(request, "approve:" + str(request.user.pk), limit=8):
        return _no_store(Response({"detail": "Too many approval attempts."}, status=429))
    if not isinstance(request.data, dict):
        return _no_store(Response({"detail": "Pairing code unavailable."}, status=404))
    code = request.data.get("verification_code")
    if not isinstance(code, str) or len(code) != 12 or not code.isascii():
        return _no_store(Response({"detail": "Pairing code unavailable."}, status=404))
    with transaction.atomic():
        pair = TerminalPairing.objects.select_for_update().filter(
            verification_code_sha256=_digest(code.upper()),
        ).first()
        if (
            pair is None or pair.status != TerminalPairing.Status.PENDING
            or pair.expires_at <= timezone.now()
        ):
            return _no_store(Response({"detail": "Pairing code unavailable."}, status=404))
        pair.user = request.user
        pair.status = TerminalPairing.Status.APPROVED
        pair.approved_at = timezone.now()
        pair.save(update_fields=["user", "status", "approved_at"])
        result = {"id": str(pair.id), "device_label": pair.device_label,
                  "expires_at": pair.expires_at.isoformat()}
    return _no_store(Response(result))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def terminal_pairings(request):
    rows = TerminalPairing.objects.filter(
        user=request.user, status=TerminalPairing.Status.APPROVED,
        expires_at__gt=timezone.now(),
    )
    return _no_store(Response({"items": [
        {"id": str(row.id), "device_label": row.device_label,
         "approved_at": row.approved_at.isoformat() if row.approved_at else None,
         "expires_at": row.expires_at.isoformat()}
        for row in rows[:30]
    ]}))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def terminal_pair_revoke(request, pairing_id):
    with transaction.atomic():
        pair = TerminalPairing.objects.select_for_update().filter(
            pk=pairing_id, user=request.user,
            status=TerminalPairing.Status.APPROVED,
        ).first()
        if pair is None:
            return _no_store(Response({"detail": "Pairing unavailable."}, status=404))
        pair.status = TerminalPairing.Status.REVOKED
        pair.revoked_at = timezone.now()
        pair.save(update_fields=["status", "revoked_at"])
    return _no_store(Response(status=204))


def _forward(request, method, path, *, body=None, key=None, response_code=200):
    user = _approved_owner(request)
    if user is None:
        return _no_store(Response({"detail": "Terminal pairing expired or revoked."}, status=401))
    try:
        result = agent_client.call(
            user, method, path, scope="agent:personal", key=key, json_body=body,
        )
    except agent_client.AgentServiceError as exc:
        return _no_store(Response({"detail": str(exc)}, status=exc.status_code))
    return _no_store(Response(result, status=response_code))


@api_view(["GET"])
@permission_classes([AllowAny])
def terminal_gateway_projects(request):
    return _forward(request, "GET", "/v1/projects")


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def terminal_gateway_conversations(request):
    if request.method == "GET":
        return _forward(request, "GET", "/v1/conversations")
    title = request.data.get("title") if isinstance(request.data, dict) else None
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 200:
        return _no_store(Response({"detail": "Title must be 1–200 characters."}, status=400))
    return _forward(
        request, "POST", "/v1/conversations",
        body={"title": title.strip()}, response_code=201,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def terminal_gateway_conversation(request, conversation_id):
    return _forward(request, "GET", f"/v1/conversations/{conversation_id}")


@api_view(["POST"])
@permission_classes([AllowAny])
def terminal_gateway_turn(request, conversation_id):
    body = request.data.get("text") if isinstance(request.data, dict) else None
    if not isinstance(body, str) or not 1 <= len(body.strip()) <= 4000:
        return _no_store(Response({"detail": "Text must be 1–4000 characters."}, status=400))
    # Idempotency is client-generated and validated; never accept author IDs.
    try:
        key = UUID(str(request.headers.get("Idempotency-Key", "")))
    except (TypeError, ValueError):
        return _no_store(Response({"detail": "Idempotency key required."}, status=400))
    return _forward(
        request, "POST", f"/v1/conversations/{conversation_id}/turns",
        body={"content": {"text": body.strip()}, "source_channel": "ssh",
              "client_message_id": str(key)},
        key=key, response_code=202,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def terminal_gateway_run(request, run_id):
    return _forward(request, "GET", f"/v1/runs/{run_id}")


@api_view(["GET"])
@permission_classes([AllowAny])
def terminal_gateway_active_memories(request):
    """Read current approved private memory through the existing pairing gate.

    Never export the memory ledger or candidate/revoked entries to Herdr.
    Authorization is rechecked on *every* request, including expiry/revocation.
    No terminal UID, user-provided tenant, hidden refresh, or local cache.
    """
    return _forward(request, "GET", "/v1/memories/retrieve")
