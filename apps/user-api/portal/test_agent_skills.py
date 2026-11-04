"""M4d: one canonical validated QP proxy for ACP-reviewed references.

This test deliberately does not approve or install any skill. ACP's signed,
owner-scoped catalog and version binding remain the authority.
"""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve

from portal.agent_client import AgentServiceError
from portal.agent_skills_api import (
    reviewed_skill_binding,
    reviewed_skill_bindings,
    reviewed_skill_catalog,
)


class ReviewedResourcesProxyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("skill-reviewer", password="test")
        self.client.force_login(self.user)

    @patch("portal.agent_skills_api.agent_client.call")
    def test_one_canonical_catalog_and_bindings_route(self, call):
        call.return_value = {"items": []}
        self.assertIs(
            resolve("/api/v1/agent/skills/catalog/").func.cls,
            reviewed_skill_catalog.cls,
        )
        self.assertIs(
            resolve("/api/v1/agent/skills/bindings/").func.cls,
            reviewed_skill_bindings.cls,
        )
        self.assertEqual(
            self.client.get("/api/v1/agent/skills/catalog/").status_code, 200,
        )
        call.assert_called_once_with(
            self.user, "GET", "/v1/skills/catalog", scope="agent:personal",
        )
        call.reset_mock()
        self.assertEqual(
            self.client.get("/api/v1/agent/skills/bindings/").status_code, 200,
        )
        call.assert_called_once_with(
            self.user, "GET", "/v1/skills/bindings", scope="agent:personal",
        )

    @patch("portal.agent_skills_api.agent_client.call")
    def test_enable_and_revoke_reach_acp_with_cas(self, call):
        url = (
            "/api/v1/agent/skills/learning.quantum-foundations"
            "/versions/0.2.0/binding/"
        )
        self.assertIs(resolve(url).func.cls, reviewed_skill_binding.cls)
        call.return_value = {"status": "enabled", "revision": 1}
        response = self.client.put(
            url, "{}", content_type="application/json", HTTP_IF_MATCH='"0"',
        )
        self.assertEqual(response.status_code, 200)
        call.assert_called_once_with(
            self.user, "PUT",
            "/v1/skills/learning.quantum-foundations/versions/0.2.0/binding",
            scope="agent:personal", if_match='"0"', json_body={},
        )
        call.reset_mock()
        call.return_value = {"status": "revoked", "revision": 2}
        self.assertEqual(
            self.client.post(
                url, "{}", content_type="application/json", HTTP_IF_MATCH='"1"',
            ).status_code, 200,
        )
        call.assert_called_once_with(
            self.user, "POST",
            "/v1/skills/learning.quantum-foundations/versions/0.2.0/revoke",
            scope="agent:personal", if_match='"1"', json_body={},
        )

    @patch("portal.agent_skills_api.agent_client.call")
    def test_unreviewed_source_is_never_automatically_enabled(self, call):
        call.side_effect = AgentServiceError(
            "Not in the trusted catalog", status_code=403,
        )
        response = self.client.put(
            "/api/v1/agent/skills/proposed.resource/versions/0.1/binding/",
            "{}", content_type="application/json", HTTP_IF_MATCH='"0"',
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("trusted catalog", response.json()["detail"])

    @patch("portal.agent_skills_api.agent_client.call")
    def test_invalid_identifier_and_stale_revision_fail_closed(self, call):
        root = "/api/v1/agent/skills/"
        for url in (
            root + "..invalid/versions/0.2.0/binding/",
            root + "valid/versions/not-a-version/binding/",
        ):
            self.assertEqual(
                self.client.put(
                    url, "{}", content_type="application/json",
                    HTTP_IF_MATCH='"0"',
                ).status_code, 400,
            )
        valid = root + "valid/versions/0.2.0/binding/"
        self.assertEqual(
            self.client.put(valid, "{}", content_type="application/json").status_code,
            400,
        )
        self.assertEqual(
            self.client.put(
                valid, "{}", content_type="application/json",
                HTTP_IF_MATCH="0",
            ).status_code, 400,
        )
        call.assert_not_called()

    @patch("portal.agent_skills_api.agent_client.call")
    def test_anonymous_access_denied_without_proxying(self, call):
        self.client.logout()
        self.assertIn(
            self.client.get("/api/v1/agent/skills/catalog/").status_code,
            {401, 403},
        )
        call.assert_not_called()
