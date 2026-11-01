from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase


class AccountSecurityContractTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="nlisa",
            email="nlisa@example.invalid",
            password="old-password-for-test",
            is_active=True,
        )
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=True,
        )
        self.client.force_login(self.user)

    def test_headless_password_change_updates_password(self):
        response = self.client.post(
            "/_allauth/browser/v1/account/password/change",
            data={
                "current_password": "old-password-for-test",
                "new_password": "new-password-for-test",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-password-for-test"))

    def test_totp_management_endpoint_returns_setup_material_when_inactive(self):
        response = self.client.get(
            "/_allauth/browser/v1/account/authenticators/totp",
        )
        self.assertEqual(response.status_code, 404, response.content)
        payload = response.json()
        self.assertTrue(payload.get("meta", {}).get("secret"))
        self.assertTrue(payload.get("meta", {}).get("totp_url"))

    def test_me_reports_unconfigured_security_factors_without_false_green(self):
        response = self.client.get("/api/v1/me/")
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertIs(data["email_verified"], True)
        self.assertIs(data["mfa_configured"], False)
        self.assertIs(data["ssh_key_registered"], False)
        self.assertIs(data["wireguard_key_registered"], False)
        self.assertIs(data["posix_provisioned"], False)

    def test_me_reports_public_key_registration_without_claiming_provisioning(self):
        from portal.models import Person, SSHKey, WireGuardKey

        person = Person.objects.create(
            user=self.user,
            given_names="Research",
            family_name="User",
            institution="CSIR",
        )
        SSHKey.objects.create(
            person=person, name="laptop", public_key="ssh-ed25519 test-placeholder",
            fingerprint="SHA256:test-registered-only", active=True,
        )
        WireGuardKey.objects.create(
            person=person, name="laptop",
            public_key="A" * 44, active=True,
        )
        response = self.client.get("/api/v1/me/")
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertIs(data["ssh_key_registered"], True)
        self.assertIs(data["wireguard_key_registered"], True)
        self.assertIs(data["wireguard_key_provisioned"], False)
        self.assertIs(data["posix_provisioned"], False)
