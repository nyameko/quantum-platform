import base64
import struct

from django.contrib.auth.models import User
from django.test import TestCase

from portal.models import Person, SSHKey, WireGuardKey


def openssh_key(key_type="ssh-ed25519", payload=b"01234567890123456789012345678901"):
    key_type_bytes = key_type.encode("ascii")
    blob = (
        struct.pack(">I", len(key_type_bytes))
        + key_type_bytes
        + struct.pack(">I", len(payload))
        + payload
    )
    return f"{key_type} {base64.b64encode(blob).decode('ascii')} test@example"


class AccessKeyApiTests(TestCase):
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
        )
        self.client.force_login(self.user)

    def test_register_and_revoke_ssh_key(self):
        response = self.client.post(
            "/api/v1/ssh-keys/",
            data={"name": "blackmyth", "public_key": openssh_key()},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        payload = response.json()
        self.assertTrue(payload["fingerprint"].startswith("SHA256:"))
        key = SSHKey.objects.get(pk=payload["id"])
        self.assertTrue(key.active)

        revoke = self.client.post(
            f"/api/v1/ssh-keys/{key.pk}/revoke/",
            data={},
            content_type="application/json",
        )
        self.assertEqual(revoke.status_code, 200, revoke.content)
        key.refresh_from_db()
        self.assertFalse(key.active)

    def test_reject_duplicate_ssh_key(self):
        key = openssh_key()
        first = self.client.post(
            "/api/v1/ssh-keys/",
            data={"name": "one", "public_key": key},
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 201, first.content)
        duplicate = self.client.post(
            "/api/v1/ssh-keys/",
            data={"name": "two", "public_key": key},
            content_type="application/json",
        )
        self.assertEqual(duplicate.status_code, 409, duplicate.content)

    def test_register_and_revoke_wireguard_key(self):
        public_key = base64.b64encode(bytes(range(32))).decode("ascii")
        response = self.client.post(
            "/api/v1/wireguard-keys/",
            data={"name": "blackmyth-wg", "public_key": public_key},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        payload = response.json()
        key = WireGuardKey.objects.get(pk=payload["id"])
        self.assertTrue(key.active)
        self.assertEqual(payload["client"]["state"], "registered")
        self.assertFalse(payload["client"]["complete"])
        self.assertIn("PrivateKey = <YOUR_PRIVATE_KEY>", payload["client"]["config"])
        self.assertIn("Address = <assigned-after-provisioning>", payload["client"]["config"])

        revoke = self.client.post(
            f"/api/v1/wireguard-keys/{key.pk}/revoke/",
            data={},
            content_type="application/json",
        )
        self.assertEqual(revoke.status_code, 200, revoke.content)
        key.refresh_from_db()
        self.assertFalse(key.active)

    def test_reject_invalid_wireguard_key(self):
        response = self.client.post(
            "/api/v1/wireguard-keys/",
            data={"name": "bad", "public_key": "not-a-wireguard-key"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)
