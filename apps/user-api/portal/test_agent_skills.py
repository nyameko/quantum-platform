"""M4d: browser never approves arbitrary skill code; ACP remains authority."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from portal.agent_client import AgentServiceError


class ReviewedResourcesProxyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("skill-reviewer", password="test")
        self.client.force_login(self.user)

    @patch("portal.agent_api.agent_client.call")
    def test_catalog_and_bindings_are_signed_owner_only(self, call):
        call.return_value = {"items": []}
        self.assertEqual(self.client.get("/api/v1/agent/skills/").status_code, 200)
        call.assert_called_with(
            self.user, "GET", "/v1/skills/catalog",
            scope="agent:personal", key=None, params=None, json_body=None,
        )
        call.reset_mock()
        self.assertEqual(
            self.client.get("/api/v1/agent/skills/bindings/").status_code, 200
        )
        call.assert_called_with(
            self.user, "GET", "/v1/skills/bindings",
            scope="agent:personal", key=None, params=None, json_body=None,
        )

    @patch("portal.agent_api.agent_client.call")
    def test_binding_revision_reaches_acp_with_owner_scope(self, call):
        url = "/api/v1/agent/skills/learning.quantum-foundations/versions/0.2.0/binding/"
        call.return_value = {"status": "enabled", "revision": 1}
        result = self.client.put(url, "{}", content_type="application/json",
                                 HTTP_IF_MATCH='"0"')
        self.assertEqual(result.status_code, 200)
        call.assert_called_with(
            self.user, "PUT",
            "/v1/skills/learning.quantum-foundations/versions/0.2.0/binding",
            scope="agent:personal", if_match='"0"', json_body={},
        )
        call.reset_mock()
        call.return_value = {"status": "revoked", "revision": 2}
        self.assertEqual(self.client.post(
            url, "{}", content_type="application/json", HTTP_IF_MATCH='"1"'
        ).status_code, 200)
        self.assertEqual(call.call_args.kwargs["if_match"], '"1"')
        self.assertEqual(call.call_args.args[1], "POST")
        self.assertEqual(call.call_args.kwargs["scope"], "agent:personal")

    @patch("portal.agent_api.agent_client.call")
    def test_proposed_or_nonreviewed_denial_is_not_auto_enabled(self, call):
        url = "/api/v1/agent/skills/proposed.resource/versions/0.1/binding/"
        call.side_effect = AgentServiceError(
            "Skill not in reviewed catalog", status_code=403,
        )
        result = self.client.put(
            url, "{}", content_type="application/json", HTTP_IF_MATCH='"0"',
        )
        self.assertEqual(result.status_code, 403)
        self.assertIn("reviewed catalog", result.json()["detail"])

    @patch("portal.agent_api.agent_client.call")
    def test_missing_revision_and_anonymous_denied(self, call):
        url = "/api/v1/agent/skills/x/versions/1.0/binding/"
        self.assertEqual(self.client.put(
            url, "{}", content_type="application/json"
        ).status_code, 400)
        call.assert_not_called()
        self.client.logout()
        self.assertIn(
            self.client.get("/api/v1/agent/skills/").status_code, {401, 403}
        )
        call.assert_not_called()
