from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase


class HeadlessLoginContractTests(TestCase):
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

    def _logout(self):
        self.client.delete("/_allauth/browser/v1/auth/session")

    def test_username_login_accepts_changed_django_password(self):
        self.user.set_password("new-password-for-test")
        self.user.save(update_fields=["password"])

        response = self.client.post(
            "/_allauth/browser/v1/auth/login",
            data={
                "username": "nlisa",
                "password": "new-password-for-test",
            },
            content_type="application/json",
        )
        self.assertIn(response.status_code, (200, 401), response.content)
        payload = response.json()
        self.assertTrue(payload.get("meta", {}).get("is_authenticated"), payload)

    def test_email_login_accepts_changed_django_password(self):
        self.user.set_password("new-password-for-test")
        self.user.save(update_fields=["password"])

        response = self.client.post(
            "/_allauth/browser/v1/auth/login",
            data={
                "email": "nlisa@example.invalid",
                "password": "new-password-for-test",
            },
            content_type="application/json",
        )
        self.assertIn(response.status_code, (200, 401), response.content)
        payload = response.json()
        self.assertTrue(payload.get("meta", {}).get("is_authenticated"), payload)

    def test_generic_login_field_is_rejected(self):
        response = self.client.post(
            "/_allauth/browser/v1/auth/login",
            data={
                "login": "nlisa",
                "password": "old-password-for-test",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)
