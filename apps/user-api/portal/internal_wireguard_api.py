import ipaddress
import secrets

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import AuditEvent, WireGuardKey


def _authorized(request):
    configured = settings.WIREGUARD_RECONCILER_TOKEN
    if not configured:
        return False
    supplied = request.headers.get("Authorization", "")
    prefix = "Bearer "
    return supplied.startswith(prefix) and secrets.compare_digest(
        supplied[len(prefix):],
        configured,
    )


def _forbidden():
    return Response(
        {"detail": "WireGuard reconciler authentication required."},
        status=status.HTTP_403_FORBIDDEN,
    )


def _pool():
    try:
        network = ipaddress.ip_network(settings.WIREGUARD_CLIENT_POOL, strict=False)
    except ValueError as exc:
        raise RuntimeError("WIREGUARD_CLIENT_POOL is not configured correctly.") from exc
    if network.version != 4:
        raise RuntimeError("M3a WireGuard allocator currently requires an IPv4 pool.")
    return network


def _allocate_address():
    network = _pool()
    assigned = set(
        WireGuardKey.objects.exclude(assigned_address="")
        .values_list("assigned_address", flat=True)
    )
    reserved = set(settings.WIREGUARD_RESERVED_ADDRESSES)

    for address in network.hosts():
        candidate = f"{address}/32"
        if candidate in assigned or str(address) in reserved or candidate in reserved:
            continue
        return candidate

    raise RuntimeError("WireGuard client address pool is exhausted.")


def _peer_payload(key):
    return {
        "id": key.pk,
        "username": key.person.user.username,
        "name": key.name,
        "public_key": key.public_key,
        "allowed_ip": key.assigned_address,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def desired_wireguard_peers(request):
    if not _authorized(request):
        return _forbidden()

    if not settings.WIREGUARD_CLIENT_POOL:
        return Response(
            {"detail": "WireGuard client pool is not configured."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    with transaction.atomic():
        keys = list(
            WireGuardKey.objects.select_for_update()
            .filter(active=True)
            .select_related("person__user")
            .order_by("created_at", "pk")
        )
        for key in keys:
            if not key.assigned_address:
                try:
                    key.assigned_address = _allocate_address()
                except RuntimeError as exc:
                    return Response(
                        {"detail": str(exc)},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
                key.provisioned_at = None
                key.save(update_fields=["assigned_address", "provisioned_at"])

    return Response(
        {
            "interface": "wg0",
            "peers": [_peer_payload(key) for key in keys],
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def acknowledge_wireguard_peers(request):
    if not _authorized(request):
        return _forbidden()

    ids = request.data.get("peer_ids")
    if not isinstance(ids, list) or any(not isinstance(value, int) for value in ids):
        return Response(
            {"detail": "peer_ids must be a list of integer key IDs."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    reconciled = list(
        WireGuardKey.objects.filter(pk__in=ids, active=True)
    )
    WireGuardKey.objects.filter(
        pk__in=[key.pk for key in reconciled],
        active=True,
    ).update(provisioned_at=now)

    for key in reconciled:
        AuditEvent.objects.create(
            actor=None,
            event_type="WIREGUARD_KEY_PROVISIONED",
            object_type="WireGuardKey",
            object_id=str(key.pk),
            metadata={"assigned_address": key.assigned_address},
        )

    return Response(
        {
            "reconciled": [key.pk for key in reconciled],
            "reconciled_at": now,
        }
    )
