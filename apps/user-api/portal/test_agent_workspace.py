"""M4c C1: signed backend-only workspace proxies."""

from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase


class WorkspaceProxyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("workspace-tester", password="test-only")
        self.client.force_login(self.user)

    @patch("portal.agent_api.agent_client.call")
    def test_project_patch_forwards_signed_identity_and_version(self, call):
        project_id = uuid4()
        call.return_value = {"id": str(project_id), "title": "Renamed"}
        response = self.client.patch(
            f"/api/v1/agent/projects/{project_id}/",
            {"title": " Renamed ", "archived": False},
            content_type="application/json",
            HTTP_IF_MATCH='"2026-10-31T00:00:00+00:00"',
        )
        self.assertEqual(response.status_code, 200)
        call.assert_called_once_with(
            self.user, "PATCH", f"/v1/projects/{project_id}",
            scope="agent:personal",
            json_body={"title": "Renamed", "archived": False},
            if_match='"2026-10-31T00:00:00+00:00"',
        )

    @patch("portal.agent_api.agent_client.call")
    def test_conversation_can_be_unfiled_but_not_moved_to_invalid_id(self, call):
        conv_id = uuid4()
        call.return_value = {"id": str(conv_id), "project_id": None}
        response = self.client.patch(
            f"/api/v1/agent/conversations/{conv_id}/",
            {"project_id": None}, content_type="application/json",
            HTTP_IF_MATCH='"2026-10-31T00:00:00+00:00"',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(call.call_args.kwargs["json_body"], {"project_id": None})
        call.reset_mock()
        invalid = self.client.patch(
            f"/api/v1/agent/conversations/{conv_id}/",
            {"project_id": "not-a-uuid"}, content_type="application/json",
            HTTP_IF_MATCH='"2026-10-31T00:00:00+00:00"',
        )
        self.assertEqual(invalid.status_code, 400)
        call.assert_not_called()

    @patch("portal.agent_api.agent_client.call")
    def test_rejects_missing_version_and_unsupported_fields(self, call):
        project_id = uuid4()
        path = f"/api/v1/agent/projects/{project_id}/"
        no_version = self.client.patch(
            path, {"title": "X"}, content_type="application/json"
        )
        self.assertEqual(no_version.status_code, 400)
        injection = self.client.patch(
            path, {"owner_subject": "other"}, content_type="application/json",
            HTTP_IF_MATCH='"2026-10-31T00:00:00+00:00"',
        )
        self.assertEqual(injection.status_code, 400)
        call.assert_not_called()

    @patch("portal.agent_api.agent_client.call")
    def test_anonymous_workspace_patch_denied(self, call):
        self.client.logout()
        response = self.client.patch(
            f"/api/v1/agent/projects/{uuid4()}/",
            {"title": "X"}, content_type="application/json",
            HTTP_IF_MATCH='"2026-10-31T00:00:00+00:00"',
        )
        self.assertIn(response.status_code, {401, 403})
        call.assert_not_called()
