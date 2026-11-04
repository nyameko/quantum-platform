"""Security contract for browser-confirmed terminal pairing, no SSH login needed."""
from datetime import timedelta
from unittest.mock import patch
from uuid import UUID, uuid4

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase
from django.utils import timezone

from portal.models import TerminalPairing


class TerminalPairingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username="owner", password="fixture")
        self.other = User.objects.create_user(username="other", password="fixture")
        self.client = Client()

    def start(self):
        response = self.client.post(
            "/api/v1/agent/terminal-pairings/start/",
            data='{"device_label":"SSH research terminal"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def headers(self, credentials):
        return {
            "HTTP_X_ACP_PAIRING_ID": credentials["pairing_id"],
            "HTTP_AUTHORIZATION": "Pairing " + credentials["pairing_proof"],
        }

    def test_browser_approval_forwards_only_signed_owner_and_revocation_blocks_next_call(self):
        created = self.start()
        list_path = "/api/v1/agent/terminal-gateway/projects/"
        self.assertEqual(self.client.get(list_path, **self.headers(created)).status_code, 401)
        self.client.force_login(self.owner)
        ok = self.client.post(
            "/api/v1/agent/terminal-pairings/approve/",
            data='{"verification_code":"' + created["verification_code"] + '"}',
            content_type="application/json",
        )
        self.assertEqual(ok.status_code, 200, ok.content)
        self.assertEqual(ok.json()["id"], created["pairing_id"])
        with patch("portal.terminal_pairing_api.agent_client.call") as gateway:
            gateway.return_value = {"items": [{"id": str(uuid4()), "title": "Private"}]}
            reply = self.client.get(list_path, **self.headers(created))
            self.assertEqual(reply.status_code, 200)
            gateway.assert_called_once_with(
                self.owner, "GET", "/v1/projects",
                scope="agent:personal", key=None, json_body=None,
            )
        owner_sessions = self.client.get("/api/v1/agent/terminal-pairings/")
        self.assertEqual(owner_sessions.status_code, 200)
        self.assertEqual(len(owner_sessions.json()["items"]), 1)
        self.assertNotIn("pairing_proof", str(owner_sessions.content))
        revoked = self.client.post(
            f"/api/v1/agent/terminal-pairings/{created['pairing_id']}/revoke/",
            data="{}", content_type="application/json",
        )
        self.assertEqual(revoked.status_code, 204)
        with patch("portal.terminal_pairing_api.agent_client.call") as gateway:
            self.assertEqual(
                self.client.get(list_path, **self.headers(created)).status_code, 401
            )
            gateway.assert_not_called()

    def test_other_authenticated_user_cannot_revoke_or_approve_same_code_twice(self):
        created = self.start()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(
            "/api/v1/agent/terminal-pairings/approve/",
            data='{"verification_code":"' + created["verification_code"] + '"}',
            content_type="application/json",
        ).status_code, 200)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(
            f"/api/v1/agent/terminal-pairings/{created['pairing_id']}/revoke/",
            data="{}", content_type="application/json",
        ).status_code, 404)
        self.assertEqual(self.client.post(
            "/api/v1/agent/terminal-pairings/approve/",
            data='{"verification_code":"' + created["verification_code"] + '"}',
            content_type="application/json",
        ).status_code, 404)

    def test_expired_and_forged_proofs_never_reach_signed_client(self):
        created = self.start()
        self.assertEqual(self.client.get(
            "/api/v1/agent/terminal-gateway/projects/",
            HTTP_X_ACP_PAIRING_ID=created["pairing_id"],
            HTTP_AUTHORIZATION="Pairing " + "x" * 45,
        ).status_code, 401)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(
            "/api/v1/agent/terminal-pairings/approve/",
            data='{"verification_code":"' + created["verification_code"] + '"}',
            content_type="application/json",
        ).status_code, 200)
        pair = TerminalPairing.objects.get(pk=UUID(created["pairing_id"]))
        pair.expires_at = timezone.now() - timedelta(seconds=1)
        pair.save(update_fields=["expires_at"])
        with patch("portal.terminal_pairing_api.agent_client.call") as gateway:
            self.assertEqual(self.client.get(
                "/api/v1/agent/terminal-gateway/projects/",
                **self.headers(created),
            ).status_code, 401)
            gateway.assert_not_called()

    def test_missing_proof_or_anonymous_browser_cannot_approve(self):
        created = self.start()
        self.assertEqual(self.client.post(
            "/api/v1/agent/terminal-pairings/approve/",
            data='{"verification_code":"' + created["verification_code"] + '"}',
            content_type="application/json",
        ).status_code, 403)
        self.assertEqual(self.client.get(
            "/api/v1/agent/terminal-gateway/projects/"
        ).status_code, 401)

    def test_terminal_turn_is_idempotent_and_source_is_ssh(self):
        created = self.start()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(
            "/api/v1/agent/terminal-pairings/approve/",
            data='{"verification_code":"' + created["verification_code"] + '"}',
            content_type="application/json",
        ).status_code, 200)
        chat = uuid4()
        key = uuid4()
        with patch("portal.terminal_pairing_api.agent_client.call") as gateway:
            gateway.return_value = {"run_id": str(uuid4()), "status": "queued"}
            response = self.client.post(
                f"/api/v1/agent/terminal-gateway/conversations/{chat}/turns/",
                data='{"text":"Inspect the Bell experiment"}',
                content_type="application/json",
                HTTP_IDEMPOTENCY_KEY=str(key),
                **self.headers(created),
            )
            self.assertEqual(response.status_code, 202)
            self.assertEqual(gateway.call_args.kwargs["key"], key)
            self.assertEqual(
                gateway.call_args.kwargs["json_body"]["source_channel"], "ssh"
            )
            self.assertEqual(
                gateway.call_args.kwargs["json_body"]["client_message_id"], str(key)
            )
