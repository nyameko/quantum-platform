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
