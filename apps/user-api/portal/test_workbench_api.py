import base64
import hashlib
import hmac
import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from portal.models import Person


class WorkbenchApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="nlisa",
            email="nlisa@example.invalid",
            password="test-password",
        )
        self.person = Person.objects.create(
            user=self.user,
            given_names="Nyameko Lisa",
            family_name="Researcher",
            institution="CSIR",
            posix_uid=20999,
            posix_gid=20999,
        )
        self.client.force_login(self.user)

    @override_settings(
        JUPYTERHUB_API_URL="http://jupyterhub/hub/api",
        JUPYTERHUB_API_TOKEN="api-token",
        JUPYTERHUB_LAUNCH_SIGNING_KEY="launch-secret",
        JUPYTERHUB_PUBLIC_URL="https://jupyter.example.invalid",
        JUPYTERHUB_LAUNCH_TOKEN_TTL=60,
    )
    def test_launch_token_contains_posix_identity_and_valid_signature(self):
        response = self.client.post(
            "/api/v1/workbench/launch/",
            data={"theme": "light"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)

        token = response.json()["launch_url"].split("token=", 1)[1]
        from urllib.parse import unquote

        encoded, signature = unquote(token).split(".", 1)
        padded = encoded + "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))

        expected = base64.urlsafe_b64encode(
            hmac.new(
                b"launch-secret",
                encoded.encode("ascii"),
                hashlib.sha256,
            ).digest()
        ).decode("ascii").rstrip("=")

        self.assertEqual(signature, expected)
        self.assertEqual(payload["sub"], "nlisa")
        self.assertEqual(payload["uid"], 20999)
        self.assertEqual(payload["gid"], 20999)
        self.assertEqual(payload["theme"], "light")
        self.assertEqual(payload["aud"], "jupyterhub-workbench")
        self.assertRegex(payload["jti"], r"^[0-9a-f]{32}$")
        self.assertLessEqual(payload["exp"] - payload["iat"], 60)

    @override_settings(
        JUPYTERHUB_API_URL="http://jupyterhub/hub/api",
        JUPYTERHUB_API_TOKEN="api-token",
        JUPYTERHUB_LAUNCH_SIGNING_KEY="launch-secret",
        JUPYTERHUB_PUBLIC_URL="https://jupyter.example.invalid",
    )
    @patch("portal.workbench_api._hub_request")
    def test_running_status_returns_open_url(self, hub_request):
        hub_request.return_value = (
            200,
            {"servers": {"": {"ready": True, "url": "/user/nlisa/"}}},
        )
        response = self.client.get("/api/v1/workbench/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["state"], "running")
        self.assertEqual(
            response.json()["open_url"],
            "https://jupyter.example.invalid/user/nlisa/",
        )

    def test_workbench_requires_posix_identity(self):
        self.person.posix_uid = None
        self.person.posix_gid = None
        self.person.save(update_fields=["posix_uid", "posix_gid"])
        response = self.client.get("/api/v1/workbench/")
        self.assertEqual(response.status_code, 409, response.content)
