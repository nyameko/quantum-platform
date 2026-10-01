import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AuditEvent


def _audit(actor, event_type, metadata=None):
    AuditEvent.objects.create(
        actor=actor,
        event_type=event_type,
        object_type="Workbench",
        object_id=actor.username,
        metadata=metadata or {},
    )


def _person(request):
    person = getattr(request.user, "person", None)
    if person is None:
        return None, Response(
            {"detail": "Complete your research profile before launching a workbench."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if person.posix_uid is None or person.posix_gid is None:
        return None, Response(
            {
                "detail": (
                    "Your research POSIX identity has not been provisioned yet. "
                    "Workbench launch is unavailable until UID/GID assignment is complete."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )
    return person, None


def _configured():
    return bool(
        settings.JUPYTERHUB_API_URL
        and settings.JUPYTERHUB_API_TOKEN
        and settings.JUPYTERHUB_LAUNCH_SIGNING_KEY
    )


def _b64url(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _launch_token(user, person, theme="dark"):
    now = int(time.time())
    payload = {
        "aud": "jupyterhub-workbench",
        "sub": user.username,
        "uid": person.posix_uid,
        "gid": person.posix_gid,
        "theme": theme if theme in {"light", "dark"} else "dark",
        "iat": now,
        "exp": now + settings.JUPYTERHUB_LAUNCH_TOKEN_TTL,
        "jti": uuid.uuid4().hex,
    }
    encoded = _b64url(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = _b64url(
        hmac.new(
            settings.JUPYTERHUB_LAUNCH_SIGNING_KEY.encode("utf-8"),
            encoded.encode("ascii"),
            hashlib.sha256,
        ).digest()
    )
    return f"{encoded}.{signature}"


def _hub_request(method, path):
    url = f"{settings.JUPYTERHUB_API_URL}/{path.lstrip('/')}"
    request = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": f"token {settings.JUPYTERHUB_API_TOKEN}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read()
        payload = None
        if body:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {"detail": body.decode("utf-8", errors="replace")}
        return exc.code, payload
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("JupyterHub API is unavailable.") from exc


def _state_from_user_model(model):
    servers = (model or {}).get("servers") or {}
    server = servers.get("") or {}

    if not server:
        return "stopped", None

    if server.get("ready"):
        return "running", server.get("url")

    pending = server.get("pending")
    if pending:
        return str(pending), server.get("url")

    return "stopped", server.get("url")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def workbench_status(request):
    person, error = _person(request)
    if error:
        return error

    if not _configured():
        return Response(
            {
                "configured": False,
                "state": "unavailable",
                "detail": "Workbench integration is not configured.",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        hub_status, model = _hub_request(
            "GET",
            f"users/{urllib.parse.quote(request.user.username, safe='')}",
        )
    except RuntimeError as exc:
        return Response(
            {"configured": True, "state": "unavailable", "detail": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    if hub_status == 404:
        state, server_url = "stopped", None
    elif hub_status == 200:
        state, server_url = _state_from_user_model(model)
    else:
        return Response(
            {
                "configured": True,
                "state": "unavailable",
                "detail": "Unable to read workbench state from JupyterHub.",
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    open_url = None
    if server_url:
        open_url = f"{settings.JUPYTERHUB_PUBLIC_URL}{server_url}"

    return Response(
        {
            "configured": True,
            "state": state,
            "open_url": open_url,
            "username": request.user.username,
            "uid": person.posix_uid,
            "gid": person.posix_gid,
            "home": f"/home/research/{request.user.username}",
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def launch_workbench(request):
    person, error = _person(request)
    if error:
        return error

    if not _configured():
        return Response(
            {"detail": "Workbench integration is not configured."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    requested_theme = str((request.data or {}).get("theme", "dark")).strip().lower()
    theme = requested_theme if requested_theme in {"light", "dark"} else "dark"
    token = _launch_token(request.user, person, theme=theme)
    launch_url = (
        f"{settings.JUPYTERHUB_PUBLIC_URL}/hub/platform-login"
        f"?token={urllib.parse.quote(token, safe='')}"
    )

    _audit(
        request.user,
        "WORKBENCH_LAUNCH_REQUESTED",
        metadata={"uid": person.posix_uid, "gid": person.posix_gid, "theme": theme},
    )

    return Response(
        {
            "launch_url": launch_url,
            "expires_in": settings.JUPYTERHUB_LAUNCH_TOKEN_TTL,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stop_workbench(request):
    person, error = _person(request)
    if error:
        return error

    if not _configured():
        return Response(
            {"detail": "Workbench integration is not configured."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        hub_status, _payload = _hub_request(
            "DELETE",
            f"users/{urllib.parse.quote(request.user.username, safe='')}/server",
        )
    except RuntimeError as exc:
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    if hub_status not in (202, 204, 404):
        return Response(
            {"detail": "JupyterHub rejected the workbench stop request."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    _audit(request.user, "WORKBENCH_STOP_REQUESTED")
    return Response({"state": "stopping" if hub_status != 404 else "stopped"})
