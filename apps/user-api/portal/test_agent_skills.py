"""M4d: ACP remains sole authority for reviewed skill sources and owner bindings."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from portal.agent_client import AgentServiceError


class ReviewedSkillProxyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("skill-tester", password="synthetic-only")
        self.client.force_login(self.user)

    @patch("portal.agent_skills_api.agent_client.call")
    def test_owner_catalog_and_bindings_are_signed_reads(self, call):
        call.return_value = {"items": []}
        self.assertEqual(
            self.client.get("/api/v1/agent/skills/catalog/").status_code, 200,
        )
        call.assert_called_with(
            self.user, "GET", "/v1/skills/catalog", scope="agent:personal",
        )
        call.reset_mock()
        self.assertEqual(
            self.client.get("/api/v1/agent/skills/bindings/").status_code, 200,
        )
        call.assert_called_with(
            self.user, "GET", "/v1/skills/bindings", scope="agent:personal",
        )

    @patch("portal.agent_skills_api.agent_client.call")
    def test_mutations_require_cas_and_cannot_change_catalog(self, call):
        root = "/api/v1/agent/skills/learning.bell/versions/0.1.0/binding/"
        call.return_value = {"status": "enabled", "revision": 1}
        no_version = self.client.put(root)
        self.assertEqual(no_version.status_code, 400)
        call.assert_not_called()
        enabled = self.client.put(root, HTTP_IF_MATCH='"0"')
        self.assertEqual(enabled.status_code, 200)
        call.assert_called_with(
            self.user, "PUT", "/v1/skills/learning.bell/versions/0.1.0/binding",
            scope="agent:personal", if_match='"0"',
        )
        call.reset_mock()
        revoked = self.client.post(root, HTTP_IF_MATCH='"1"')
        self.assertEqual(revoked.status_code, 200)
        call.assert_called_with(
            self.user, "POST", "/v1/skills/learning.bell/versions/0.1.0/revoke",
            scope="agent:personal", if_match='"1"',
        )

    @patch("portal.agent_skills_api.agent_client.call")
    def test_invalid_ids_and_unreviewed_deny_without_escalation(self, call):
        bad = "/api/v1/agent/skills/NOT-REVIEWED/versions/0.1.0/binding/"
        self.assertEqual(
            self.client.put(bad, HTTP_IF_MATCH='"0"').status_code, 400,
        )
        call.assert_not_called()
        call.side_effect = AgentServiceError(
            "This resource is not approved or authorized.", status_code=403,
        )
        denied = self.client.put(
            "/api/v1/agent/skills/learning.bell/versions/0.1.0/binding/",
            HTTP_IF_MATCH='"0"',
        )
        self.assertEqual(denied.status_code, 403)

    @patch("portal.agent_skills_api.agent_client.call")
    def test_anonymous_cannot_list_or_mutate(self, call):
        self.client.logout()
        for path in ("/api/v1/agent/skills/catalog/",
                     "/api/v1/agent/skills/bindings/"):
            self.assertIn(self.client.get(path).status_code, {401, 403})
        self.assertIn(
            self.client.put(
                "/api/v1/agent/skills/learning.bell/versions/0.1.0/binding/",
                HTTP_IF_MATCH='"0"',
            ).status_code, {401, 403},
        )
        call.assert_not_called()
