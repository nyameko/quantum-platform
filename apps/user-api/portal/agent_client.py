"""Server-side ACP client. Tokens and internal addresses never reach the browser."""

import json
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
import jwt
from django.conf import settings

from .models import AgentPrincipal


class AgentServiceError(Exception):
    pass


def assertion(user):
    if not user.is_active or not user.is_staff:
        raise AgentServiceError("Administrator access is required.")
    principal, _ = AgentPrincipal.objects.get_or_create(user=user)
    now = int(time.time())
    try:
        key = Path(settings.AGENT_CONTROL_PLANE_SIGNING_KEY_FILE).read_text()
        return jwt.encode(
            {
                "iss": "quantum-platform",
                "aud": "agent-control-plane",
                "sub": f"urn:quantum-platform:user:{principal.pk}",
                "tenant": settings.AGENT_CONTROL_PLANE_TENANT,
                "scope": "admin:diagnostics",
                "iat": now,
                "nbf": now,
                "exp": now + 60,
                "jti": str(uuid4()),
            },
            key,
            algorithm="EdDSA",
        )
    except (OSError, ValueError, jwt.PyJWTError):
        raise AgentServiceError("The agent service signing key is not configured.") from None


def call(user, method, path, *, key=None, offset=0):
    base = settings.AGENT_CONTROL_PLANE_URL
    url = urlsplit(base)
    if (
        url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise AgentServiceError("The agent service has not been enabled.")
    headers = {"Authorization": f"Bearer {assertion(user)}", "Accept": "application/json"}
    kwargs = (
        {"params": {"offset": offset}}
        if method == "GET"
        else {
            "json": {"diagnostic": "quantum-platform-pod-readiness"},
        }
    )
    if key is not None:
        headers["Idempotency-Key"] = str(key)
    try:
        with (
            httpx.Client(timeout=10, follow_redirects=False, trust_env=False) as client,
            client.stream(method, base + path, headers=headers, **kwargs) as response,
        ):
            if response.status_code == 429:
                raise AgentServiceError("A diagnostic is already active, or the queue is full.")
            if response.status_code not in {200, 202}:
                raise AgentServiceError("The agent service is unavailable. Please try again.")
            body = bytearray()
            for chunk in response.iter_bytes(chunk_size=4096):
                body.extend(chunk)
                if len(body) > 2_000_000:
                    raise AgentServiceError("The agent service response was too large.")
            return json.loads(body)
    except (httpx.HTTPError, ValueError):
        raise AgentServiceError(
            "The agent service could not be reached. Please try again."
        ) from None
