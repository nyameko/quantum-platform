"""Researcher-facing M4a proxy to ACP canonical personal-agent APIs."""

from uuid import UUID, uuid4

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import agent_client


def _call(request, method, path, *, key=None, params=None, body=None):
    try:
        return Response(
            agent_client.call(
                request.user,
                method,
                path,
                scope="agent:personal",
                key=key,
                params=params,
                json_body=body,
            ),
            status=status.HTTP_201_CREATED if method == "POST" else status.HTTP_200_OK,
        )
    except agent_client.AgentServiceError as exc:
        message = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in message.lower()
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response({"detail": message}, status=code)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def agent_projects(request):
    if request.method == "GET":
        return _call(request, "GET", "/v1/projects")
    title = str(request.data.get("title", "")).strip()
    if not title:
        return Response({"detail": "Project title is required."}, status=400)
    return _call(request, "POST", "/v1/projects", body={"title": title})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def agent_conversations(request):
    if request.method == "GET":
        params = {}
        project_id = request.query_params.get("project_id")
        if project_id:
            try:
                params["project_id"] = str(UUID(project_id))
            except ValueError:
                return Response({"detail": "Invalid project ID."}, status=400)
        return _call(request, "GET", "/v1/conversations", params=params)

    title = str(request.data.get("title", "")).strip()
    if not title:
        return Response({"detail": "Conversation title is required."}, status=400)
    body = {"title": title}
    project_id = request.data.get("project_id")
    if project_id:
        try:
            body["project_id"] = str(UUID(str(project_id)))
        except ValueError:
            return Response({"detail": "Invalid project ID."}, status=400)
    return _call(request, "POST", "/v1/conversations", body=body)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def agent_conversation(request, conversation_id):
    return _call(request, "GET", f"/v1/conversations/{conversation_id}")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agent_turn(request, conversation_id):
    content = request.data.get("content")
    if content in (None, "", [], {}):
        return Response({"detail": "Message content is required."}, status=400)
    source_channel = str(request.data.get("source_channel", "web"))
    if source_channel != "web":
        return Response({"detail": "Portal turns must use the web channel."}, status=400)
    client_message_id = request.data.get("client_message_id")
    try:
        key = UUID(request.headers.get("Idempotency-Key", "")) if request.headers.get(
            "Idempotency-Key"
        ) else uuid4()
    except ValueError:
        return Response({"detail": "Invalid idempotency key."}, status=400)

    body = {"content": content, "source_channel": "web"}
    if client_message_id:
        body["client_message_id"] = str(client_message_id)[:200]
    response = _call(
        request,
        "POST",
        f"/v1/conversations/{conversation_id}/turns",
        key=key,
        body=body,
    )
    if response.status_code == status.HTTP_201_CREATED:
        response.status_code = status.HTTP_202_ACCEPTED
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def agent_run(request, run_id):
    return _call(request, "GET", f"/v1/runs/{run_id}")
