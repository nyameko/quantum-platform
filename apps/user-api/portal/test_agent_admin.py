import tempfile
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings

from .agent_client import AgentServiceError, assertion
from .models import AgentPrincipal


class AgentAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("operator", is_staff=True, password="test-only")
        self.user = User.objects.create_user("researcher", password="test-only")
        self.client.defaults["HTTP_HOST"] = "admin.quantum.nyameko.com"

    @patch("portal.agent_client.call")
    def test_anonymous_nonstaff_and_public_host_cannot_query(self, call):
        self.assertEqual(self.client.get("/admin/agent-runs/").status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/admin/agent-runs/").status_code, 302)
        self.client.force_login(self.admin)
        self.assertEqual(
            self.client.get("/admin/agent-runs/", HTTP_HOST="quantum.nyameko.com").status_code, 404
        )
        call.assert_not_called()

    @patch("portal.agent_client.call")
    def test_csrf_and_http_method_gates(self, call):
        client = Client(enforce_csrf_checks=True, HTTP_HOST="admin.quantum.nyameko.com")
        client.force_login(self.admin)
        self.assertEqual(
            client.post("/admin/agent-runs/", {"idempotency_key": str(uuid4())}).status_code, 403
        )
        self.assertEqual(self.client.delete("/admin/agent-runs/").status_code, 302)
        call.assert_not_called()

    @patch("portal.agent_client.call")
    def test_create_redirect_and_history(self, call):
        task_id, key = str(uuid4()), uuid4()
        call.return_value = {"task_id": task_id}
        self.client.force_login(self.admin)
        response = self.client.post("/admin/agent-runs/", {"idempotency_key": str(key)})
        self.assertRedirects(
            response, f"/admin/agent-runs/{task_id}/", fetch_redirect_response=False
        )
        call.assert_called_once_with(self.admin, "POST", "/v1/admin/tasks", key=key)
        call.return_value = {"items": []}
        self.assertContains(self.client.get("/admin/agent-runs/"), "No diagnostic tasks")

    @patch("portal.agent_client.call")
    def test_generated_output_is_escaped(self, call):
        task_id = str(uuid4())
        call.return_value = {
            "task_id": task_id,
            "run_id": str(uuid4()),
            "status": "succeeded",
            "summary": "<script>alert(1)</script>",
            "evidence": {"counts": {}},
            "events": [],
            "profile": "admin-readonly",
        }
        self.client.force_login(self.admin)
        response = self.client.get(f"/admin/agent-runs/{task_id}/")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

    @patch("portal.agent_client.call", side_effect=AgentServiceError("Service unavailable"))
    def test_failure_preserves_idempotency_key(self, call):
        self.client.force_login(self.admin)
        key = str(uuid4())
        response = self.client.post("/admin/agent-runs/", {"idempotency_key": key})
        self.assertContains(response, key, status_code=503)
        self.assertContains(response, "Service unavailable", status_code=503)

    def test_assertion_uses_persistent_uuid_and_rechecks_staff(self):
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
                first = assertion(self.admin)
                self.admin.username = "renamed"
                self.admin.save()
                second = assertion(self.admin)
                claims = [
                    jwt.decode(
                        token,
                        key.public_key(),
                        algorithms=["EdDSA"],
                        audience="agent-control-plane",
                        issuer="quantum-platform",
                    )
                    for token in [first, second]
                ]
                self.assertEqual(claims[0]["sub"], claims[1]["sub"])
                self.assertEqual(claims[0]["scope"], "admin:diagnostics")
                self.assertEqual(claims[0]["exp"] - claims[0]["iat"], 60)
                self.assertEqual(AgentPrincipal.objects.count(), 1)
                self.admin.is_staff = False
                with self.assertRaises(AgentServiceError):
                    assertion(self.admin)
