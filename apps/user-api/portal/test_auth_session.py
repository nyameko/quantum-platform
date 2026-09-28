from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase


class PortalLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="researcher",
            email="researcher@example.invalid",
            password="test-only",
        )

    def test_logout_flushes_authenticated_session(self):
        client = Client()
        client.force_login(self.user)
        self.assertIn("_auth_user_id", client.session)
        self.assertEqual(client.post("/api/v1/logout/").status_code, 200)
        self.assertNotIn("_auth_user_id", client.session)

    def test_logout_is_idempotent_when_anonymous(self):
        self.assertEqual(Client().post("/api/v1/logout/").status_code, 200)


class RenameSystemUsernameTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="legacy-name",
            email="identity@example.invalid",
            password="test-only",
        )

    def test_dry_run_does_not_mutate(self):
        output = StringIO()
        call_command("rename_system_username", "--from", "legacy-name", "--to", "system-name", stdout=output)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "legacy-name")
        self.assertIn("DRY RUN", output.getvalue())

    def test_apply_preserves_primary_key(self):
        original_id = self.user.pk
        call_command(
            "rename_system_username",
            "--from", "legacy-name",
            "--to", "system-name",
            "--expected-email", "identity@example.invalid",
            "--apply",
            stdout=StringIO(),
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.pk, original_id)
        self.assertEqual(self.user.username, "system-name")

    def test_existing_target_is_rejected(self):
        User.objects.create_user(username="system-name", password="x")
        with self.assertRaises(CommandError):
            call_command("rename_system_username", "--from", "legacy-name", "--to", "system-name", stdout=StringIO())
