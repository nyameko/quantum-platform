from django.contrib.auth.models import User
from allauth.account import app_settings
from django.test import TestCase
from allauth.account.models import EmailAddress
from allauth.account.utils import user_pk_to_url_str


class HeadlessPasswordResetContractTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="researcher",
            email="researcher@example.invalid",
            password="old-password-for-test",
        )
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=True,
        )

    def _key(self):
        uid = user_pk_to_url_str(self.user)
        token = app_settings.PASSWORD_RESET_TOKEN_GENERATOR().make_token(self.user)
        return f"{uid}-{token}"

    def test_headless_reset_key_validates_and_changes_password(self):
        key = self._key()

        validation = self.client.get(
            "/_allauth/browser/v1/auth/password/reset",
            HTTP_X_PASSWORD_RESET_KEY=key,
        )
        self.assertEqual(validation.status_code, 200, validation.content)

        reset = self.client.post(
            "/_allauth/browser/v1/auth/password/reset",
            data={"key": key, "password": "A-new-test-password-928!"},
            content_type="application/json",
        )
        self.assertIn(reset.status_code, (200, 401), reset.content)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("A-new-test-password-928!"))

    def test_reset_key_is_invalid_after_successful_reset(self):
        key = self._key()
        response = self.client.post(
            "/_allauth/browser/v1/auth/password/reset",
            data={"key": key, "password": "Another-test-password-928!"},
            content_type="application/json",
        )
        self.assertIn(response.status_code, (200, 401), response.content)

        validation = self.client.get(
            "/_allauth/browser/v1/auth/password/reset",
            HTTP_X_PASSWORD_RESET_KEY=key,
        )
        self.assertEqual(validation.status_code, 400, validation.content)
