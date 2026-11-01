"""Portable profile proxy uses the existing owner-authenticated ACP service."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase


class AgentProfileProxyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="profile-researcher", password="test")
        self.client.force_login(self.user)

    @patch("portal.agent_api.agent_client.call")
    def test_profile_get_is_owner_scoped(self, upstream):
        upstream.return_value = {"profile": None}
        response = self.client.get("/api/v1/agent/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(upstream.call_args.args[0], self.user)
        self.assertEqual(upstream.call_args.kwargs["scope"], "agent:personal")
        self.assertEqual(upstream.call_args.args[2], "/v1/profile")

    @patch("portal.agent_api.agent_client.call")
    def test_profile_put_uses_revision_and_cannot_forge_other_fields(self, upstream):
        upstream.return_value = {"revision": 1}
        path = "/api/v1/agent/profile/"
        response = self.client.put(
            path, data={
                "display_name": " Research assistant ",
                "instructions": "Prefer mathematical derivations",
                "model_route": "reasoning",
            },
            HTTP_IF_MATCH='"0"',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(upstream.call_args.kwargs["if_match"], '"0"')
        self.assertEqual(upstream.call_args.kwargs["scope"], "agent:personal")
        self.assertEqual(upstream.call_args.kwargs["json_body"]["display_name"], "Research assistant")
        upstream.reset_mock()
        forbidden = self.client.put(
            path, data={
                "display_name": "Assistant", "credentials": "stolen",
                "model_route": "general",
            }, HTTP_IF_MATCH='"0"', content_type="application/json",
        )
        self.assertEqual(forbidden.status_code, 400)
        upstream.assert_not_called()
        stale = self.client.put(
            path, data={"display_name": "Assistant"}, content_type="application/json",
        )
        self.assertEqual(stale.status_code, 400)
        upstream.assert_not_called()

    def test_profile_unauthenticated_is_denied(self):
        self.client.logout()
        self.assertIn(
            self.client.get("/api/v1/agent/profile/").status_code, {401, 403}
        )
