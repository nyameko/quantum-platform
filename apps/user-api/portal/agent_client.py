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
    def __init__(self, message, *, status_code=503):
        super().__init__(message)
        self.status_code = status_code


def assertion(user, *, scope="admin:diagnostics"):
    if not user.is_active:
        raise AgentServiceError("An active Quantum Platform account is required.")
    if scope == "admin:diagnostics" and not user.is_staff:
        raise AgentServiceError("Administrator access is required.")
    if scope not in {"admin:diagnostics", "agent:personal"}:
        raise AgentServiceError("Unsupported agent service scope.")

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
                "scope": scope,
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


def call(
    user,
    method,
    path,
    *,
    scope="admin:diagnostics",
    key=None,
    offset=None,
    params=None,
    json_body=None,
    if_match=None,
):
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

    headers = {
        "Authorization": f"Bearer {assertion(user, scope=scope)}",
        "Accept": "application/json",
    }
    query = dict(params or {})
    if offset is not None:
        query["offset"] = offset

    kwargs = {"params": query}
    if method != "GET":
        kwargs["json"] = (
            json_body
            if json_body is not None
            else {"diagnostic": "quantum-platform-pod-readiness"}
        )
    if key is not None:
        headers["Idempotency-Key"] = str(key)
    if if_match is not None:
        headers["If-Match"] = if_match

    try:
        with (
            httpx.Client(timeout=10, follow_redirects=False, trust_env=False) as client,
            client.stream(method, base + path, headers=headers, **kwargs) as response,
        ):
            if response.status_code == 429:
                raise AgentServiceError("The agent service queue is temporarily full.")
            if response.status_code == 404:
                raise AgentServiceError(
                    "The requested agent resource was not found.", status_code=404
                )
            if response.status_code in {409, 412, 422}:
                # Bounded, user-actionable revision/conflict errors for memory and workspaces.
                raw = response.read()
                detail = (
                    "Workspace has changed; refresh before editing"
                    if response.status_code == 412
                    else "Revision conflict" if response.status_code == 409 else "Invalid request"
                )
                if len(raw) <= 8192:
                    try:
                        candidate = json.loads(raw).get("detail")
                        if isinstance(candidate, str) and len(candidate) <= 500:
                            detail = candidate
                    except (ValueError, AttributeError):
                        pass
                raise AgentServiceError(detail, status_code=response.status_code)
            if response.status_code not in {200, 201, 202}:
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
