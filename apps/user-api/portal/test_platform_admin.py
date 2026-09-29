from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase


class EnsurePlatformAdminTests(TestCase):
    def test_dry_run_does_not_create_user(self):
        output = StringIO()
        call_command(
            "ensure_platform_admin",
            "--username", "platform-admin",
            "--email", "admin@example.invalid",
            stdout=output,
        )
        self.assertFalse(User.objects.filter(username="platform-admin").exists())
        self.assertIn("DRY RUN", output.getvalue())

    def test_apply_creates_superuser(self):
        call_command(
            "ensure_platform_admin",
            "--username", "platform-admin",
            "--email", "admin@example.invalid",
            "--password", "temporary-test-password",
            "--apply",
            stdout=StringIO(),
        )
        user = User.objects.get(username="platform-admin")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("temporary-test-password"))

    def test_apply_reconciles_existing_user_without_duplicate(self):
        original = User.objects.create_user(
            username="platform-admin",
            email="old@example.invalid",
            password="old-password",
        )
        call_command(
            "ensure_platform_admin",
            "--username", "platform-admin",
            "--email", "admin@example.invalid",
            "--apply",
            stdout=StringIO(),
        )
        user = User.objects.get(username="platform-admin")
        self.assertEqual(user.pk, original.pk)
        self.assertEqual(user.email, "admin@example.invalid")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
