"""Read-only export of one researcher's portal-approved public SSH keys.

The output is an INPUT to an independently approved private Ansible inventory;
it never grants scheduler access, installs keys, or exposes private material.
"""

import json
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from portal.models import ProgrammeMembership, ResearchProgramme, SSHKey


class Command(BaseCommand):
    help = (
        "Export a single researcher's provisioned UID/GID and ACTIVE SSH public keys "
        "for explicit operator verification before Slurm login-key reconciliation."
    )

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        username = options["username"]
        if not re.fullmatch(r"[a-z_][a-z0-9_-]*", username):
            raise CommandError("Invalid POSIX research username.")

        User = get_user_model()
        user = User.objects.filter(username=username, is_active=True).first()
        if user is None:
            raise CommandError("Researcher does not exist or is disabled.")

        person = getattr(user, "person", None)
        if person is None or person.posix_uid is None or person.posix_gid is None:
            raise CommandError("Researcher lacks a provisioned POSIX UID/GID.")

        if person.posix_uid < 20000 or person.posix_gid < 20000:
            raise CommandError("Researcher numeric UID/GID is not in the research allocation range.")

        if not ProgrammeMembership.objects.filter(
            person=person,
            status=ProgrammeMembership.Status.APPROVED,
            programme__status=ResearchProgramme.Status.ACTIVE,
        ).exists():
            raise CommandError("Researcher has no approved membership in an active programme.")

        active_keys = list(
            SSHKey.objects.filter(person=person, active=True)
            .order_by("id")
            .values_list("public_key", flat=True)
        )
        if not active_keys:
            raise CommandError("No active SSH public keys are registered for this researcher.")

        # A malformed/admin-inserted key must not be serialized directly into
        # sshd authorized_keys. Portal HTTP registration also validates keys.
        for key in active_keys:
            parts = key.split()
            if (
                "\n" in key or "\r" in key or
                len(parts) < 2 or parts[0] not in {
                    "ssh-ed25519", "ssh-rsa", "ecdsa-sha2-nistp256",
                    "ecdsa-sha2-nistp384", "ecdsa-sha2-nistp521",
                    "sk-ssh-ed25519@openssh.com",
                    "sk-ecdsa-sha2-nistp256@openssh.com",
                }
            ):
                raise CommandError("An active SSH key is malformed; fix the record before export.")

        # Deliberately NO 'execution_enabled: true': programme approval and key
        # registration alone do not imply ACE Slurm resource admission.
        self.stdout.write(json.dumps({
            "username": username,
            "uid": person.posix_uid,
            "gid": person.posix_gid,
            "ssh_public_keys": active_keys,
            "site_execution_approval_required": True,
        }, indent=2))
