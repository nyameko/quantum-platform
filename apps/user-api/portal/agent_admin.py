import json
from uuid import uuid4

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_GET, require_http_methods

from . import agent_client


class DiagnosticForm(forms.Form):
    idempotency_key = forms.UUIDField(widget=forms.HiddenInput)


def private_admin(request):
    if request.get_host().split(":", 1)[0] != settings.AGENT_ADMIN_HOST:
        raise Http404
    if not request.user.is_active or not request.user.is_staff:
        raise Http404


@require_http_methods(["GET", "POST"])
def agent_history(request):
    private_admin(request)
    form = DiagnosticForm(
        request.POST if request.method == "POST" else None, initial={"idempotency_key": uuid4()}
    )
    error, rows, status = None, [], 200
    try:
        offset = min(max(int(request.GET.get("offset", "0")), 0), 10000)
    except ValueError:
        offset = 0
    if request.method == "POST":
        if form.is_valid():
            try:
                result = agent_client.call(
                    request.user,
                    "POST",
                    "/v1/admin/tasks",
                    key=form.cleaned_data["idempotency_key"],
                )
                messages.success(
                    request, "Diagnostic queued. Refresh the task page for its result."
                )
                return redirect("agent-task", task_id=result["task_id"])
            except agent_client.AgentServiceError as exc:
                error, status = str(exc), 503
        else:
            status = 400
    try:
        rows = agent_client.call(request.user, "GET", "/v1/admin/tasks", offset=offset)["items"]
    except agent_client.AgentServiceError as exc:
        error, status = error or str(exc), 503
    return TemplateResponse(
        request,
        "admin/agent_history.html",
        {
            **admin.site.each_context(request),
            "title": "Infrastructure diagnostics",
            "form": form,
            "tasks": rows,
            "service_error": error,
            "previous_offset": max(0, offset - 50),
            "offset": offset,
            "next_offset": offset + 50 if len(rows) == 50 and offset < 10000 else None,
        },
        status=status,
    )


@require_GET
def agent_task(request, task_id):
    private_admin(request)
    result, error = None, None
    try:
        result = agent_client.call(request.user, "GET", f"/v1/admin/tasks/{task_id}")
    except agent_client.AgentServiceError as exc:
        error = str(exc)
    return TemplateResponse(
        request,
        "admin/agent_task.html",
        {
            **admin.site.each_context(request),
            "title": "Diagnostic task",
            "task": result,
            "service_error": error,
            "evidence_json": json.dumps(result.get("evidence"), indent=2) if result else "",
        },
        status=503 if error else 200,
    )
