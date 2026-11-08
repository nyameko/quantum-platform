"""P0 private-inventory inputs: public keys only, never implied Slurm admission."""

import io
import json

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from portal.models import (
    Person,
    ProgrammeMembership,
    ResearchProgramme,
    SSHKey,
)


KEY_ACTIVE = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC3UqSGfF26utUBxrXbG8CY1DdS6cJIXrw0ynDeaFnC6 active"
KEY_REVOKED = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEKkXquZvA15t6AgjPqz2a6VtY3aQLLrJWfrCHHqoDPs revoked"


class SlurmPublicKeyExportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="nlisa", password="unused", is_active=True)
        self.person = Person.objects.create(
            user=self.user,
            given_names="Pilot",
            family_name="Researcher",
            institution="CHPC",
            posix_uid=20999,
            posix_gid=20999,
        )
        self.programme = ResearchProgramme.objects.create(
            name="P0 CPU Science Pilot",
            institution="CHPC",
            pi=self.person,
            status=ResearchProgramme.Status.ACTIVE,
        )
        self.membership = ProgrammeMembership.objects.create(
            person=self.person,
            programme=self.programme,
            status=ProgrammeMembership.Status.APPROVED,
        )
        SSHKey.objects.create(
            person=self.person, name="active", public_key=KEY_ACTIVE,
            fingerprint="SHA256:active-key", active=True,
        )
        SSHKey.objects.create(
            person=self.person, name="revoked", public_key=KEY_REVOKED,
            fingerprint="SHA256:revoked-key", active=False,
        )

    def export(self):
        output = io.StringIO()
        call_command("export_slurm_researcher_public_keys", "nlisa", stdout=output)
        return json.loads(output.getvalue())

    def test_exports_only_active_public_keys_and_no_execution_authority(self):
        data = self.export()
        self.assertEqual((data["uid"], data["gid"]), (20999, 20999))
        self.assertEqual(data["ssh_public_keys"], [KEY_ACTIVE])
        self.assertTrue(data["site_execution_approval_required"])
        self.assertNotIn("execution_enabled", data)
        self.assertNotIn("password", output_string := json.dumps(data).lower())
        self.assertNotIn("private_key", output_string)
        self.assertNotIn("revoked", output_string)

    def test_revocation_removes_key_from_next_export(self):
        SSHKey.objects.filter(person=self.person, active=True).update(active=False)
        with self.assertRaises(CommandError):
            self.export()

    def test_programme_suspension_denies_export(self):
        self.membership.status = ProgrammeMembership.Status.SUSPENDED
        self.membership.save(update_fields=["status"])
        with self.assertRaises(CommandError):
            self.export()

    def test_archived_programme_denies_export(self):
        self.programme.status = ResearchProgramme.Status.ARCHIVED
        self.programme.save(update_fields=["status"])
        with self.assertRaises(CommandError):
            self.export()

    def test_disabled_user_denies_export(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        with self.assertRaises(CommandError):
            self.export()

    def test_missing_uid_denies_export(self):
        self.person.posix_uid = None
        self.person.save(update_fields=["posix_uid"])
        with self.assertRaises(CommandError):
            self.export()

    def test_unknown_username_denies_export(self):
        with self.assertRaises(CommandError):
            call_command("export_slurm_researcher_public_keys", "no-one")

    def test_root_username_is_not_researcher(self):
        with self.assertRaises(CommandError):
            call_command("export_slurm_researcher_public_keys", "root")
