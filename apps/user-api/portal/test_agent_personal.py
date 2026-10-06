import tempfile
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from .agent_client import assertion
from .models import AgentPrincipal


class PersonalAgentApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("researcher", password="test-only")
        self.client.force_login(self.user)

    @patch("portal.agent_api.agent_client.call")
    def test_project_and_conversation_requests_use_personal_scope(self, call):
        project_id = str(uuid4())
        conversation_id = str(uuid4())
        call.side_effect = [
            {"id": project_id, "title": "M4 Persistence Test"},
            {
                "id": conversation_id,
                "project_id": project_id,
                "title": "Persistence Drill",
            },
        ]

        project = self.client.post(
            "/api/v1/agent/projects/",
            {"title": "M4 Persistence Test"},
            content_type="application/json",
        )
        self.assertEqual(project.status_code, 201)
        call.assert_any_call(
            self.user,
            "POST",
            "/v1/projects",
            scope="agent:personal",
            key=None,
            params=None,
            json_body={"title": "M4 Persistence Test"},
        )

        conversation = self.client.post(
            "/api/v1/agent/conversations/",
            {"title": "Persistence Drill", "project_id": project_id},
            content_type="application/json",
        )
        self.assertEqual(conversation.status_code, 201)
        call.assert_any_call(
            self.user,
            "POST",
            "/v1/conversations",
            scope="agent:personal",
            key=None,
            params=None,
            json_body={"title": "Persistence Drill", "project_id": project_id},
        )

    @patch("portal.agent_api.agent_client.call")
    def test_turn_uses_web_channel_and_idempotency_key(self, call):
        conversation_id, run_id = uuid4(), uuid4()
        key = uuid4()
        call.return_value = {"run_id": str(run_id), "status": "queued"}

        response = self.client.post(
            f"/api/v1/agent/conversations/{conversation_id}/turns/",
            {
                "content": {"text": "ACP-PERSIST-7F31"},
                "source_channel": "web",
                "client_message_id": "portal-1",
            },
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY=str(key),
        )
        self.assertEqual(response.status_code, 202)
        call.assert_called_once_with(
            self.user,
            "POST",
            f"/v1/conversations/{conversation_id}/turns",
            scope="agent:personal",
            key=key,
            params=None,
            json_body={
                "content": {"text": "ACP-PERSIST-7F31"},
                "source_channel": "web",
                "client_message_id": "portal-1",
            },
        )

    @patch("portal.agent_api.agent_client.call")
    def test_anonymous_user_cannot_proxy_personal_agent(self, call):
        self.client.logout()
        response = self.client.get("/api/v1/agent/projects/")
        self.assertIn(response.status_code, {401, 403})
        call.assert_not_called()

    def test_personal_assertion_uses_stable_agent_principal(self):
        key = Ed25519PrivateKey.generate()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.pem"
            path.write_bytes(
                key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            with override_settings(AGENT_CONTROL_PLANE_SIGNING_KEY_FILE=str(path)):
                token = assertion(self.user, scope="agent:personal")
                claims = jwt.decode(
                    token,
                    key.public_key(),
                    algorithms=["EdDSA"],
                    audience="agent-control-plane",
                    issuer="quantum-platform",
                )

        principal = AgentPrincipal.objects.get(user=self.user)
        self.assertEqual(
            claims["sub"],
            f"urn:quantum-platform:user:{principal.pk}",
        )
        self.assertEqual(claims["scope"], "agent:personal")
        UUID(claims["sub"].rsplit(":", 1)[1])
