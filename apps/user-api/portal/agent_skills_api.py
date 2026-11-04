"""Owner-scoped read-only reviewed skill catalog and explicit binding proxy.

The ACP packaged catalog, not the browser, determines trust. This proxy
cannot approve a new source, execute a notebook, allocate compute or grant
the assistant tools.
"""
import re

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import agent_client

SKILL_ID = re.compile(r"^[a-z][a-z0-9_.-]{0,119}$")
SKILL_VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}(?:[-.][a-z0-9]+)*$")


def _proxy(request, method, path, *, version=None):
    try:
        kwargs = {"scope": "agent:personal"}
        if version is not None:
            kwargs["if_match"] = version
        result = agent_client.call(request.user, method, path, **kwargs)
        return Response(result, status=200)
    except agent_client.AgentServiceError as exc:
        return Response({"detail": str(exc)}, status=exc.status_code)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reviewed_skill_catalog(request):
    return _proxy(request, "GET", "/v1/skills/catalog")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reviewed_skill_bindings(request):
    return _proxy(request, "GET", "/v1/skills/bindings")


@api_view(["PUT", "POST"])
@permission_classes([IsAuthenticated])
def reviewed_skill_binding(request, skill_id, version):
    """Enable/revoke only an ACP Git allow-listed version via CAS revision."""
    if not SKILL_ID.fullmatch(skill_id) or not SKILL_VERSION.fullmatch(version):
        return Response({"detail": "Invalid immutable skill identifier."}, status=400)
    quoted = request.headers.get("If-Match", "")
    if (
        not quoted.startswith('"') or not quoted.endswith('"')
        or not quoted[1:-1].isdecimal()
        or not 1 <= len(quoted[1:-1]) <= 8
    ):
        return Response({"detail": "Quoted current skill revision required."}, status=400)
    if request.method == "PUT":
        return _proxy(
            request, "PUT", f"/v1/skills/{skill_id}/versions/{version}/binding",
            version=quoted,
        )
    return _proxy(
        request, "POST", f"/v1/skills/{skill_id}/versions/{version}/revoke",
        version=quoted,
    )
