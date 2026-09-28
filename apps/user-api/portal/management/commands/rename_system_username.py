from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.models import AgentPrincipal, Person, ProgrammeMembership


class Command(BaseCommand):
    help = "Rename a system username safely. Dry-run by default."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="source", required=True)
        parser.add_argument("--to", dest="target", required=True)
        parser.add_argument("--expected-email", dest="expected_email")
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        User = get_user_model()
        source = options["source"].strip()
        target = options["target"].strip()
        expected_email = (options.get("expected_email") or "").strip()

        if source == target:
            raise CommandError("Source and target usernames are identical.")

        user = User.objects.filter(username=source).first()
        if user is None:
            raise CommandError(f"Source user {source!r} does not exist.")

        if User.objects.filter(username=target).exclude(pk=user.pk).exists():
            raise CommandError(f"Target username {target!r} already exists.")

        if expected_email and user.email.lower() != expected_email.lower():
            raise CommandError("Email does not match --expected-email; refusing rename.")

        person = Person.objects.filter(user=user).first()
        memberships = ProgrammeMembership.objects.filter(person__user=user).count()
        principal = AgentPrincipal.objects.filter(user=user).first()

        self.stdout.write(f"user_id={user.pk}")
        self.stdout.write(f"username={source!r} -> {target!r}")
        self.stdout.write(f"email={user.email!r}")
        self.stdout.write(f"person_id={person.pk if person else None}")
        self.stdout.write(f"programme_memberships={memberships}")
        self.stdout.write(f"agent_principal={principal.pk if principal else None}")

        if not options["apply"]:
            self.stdout.write(self.style.WARNING("DRY RUN: no changes made. Re-run with --apply."))
            return

        with transaction.atomic():
            locked = User.objects.select_for_update().get(pk=user.pk)
            if locked.username != source:
                raise CommandError("Username changed concurrently; refusing rename.")
            locked.username = target
            locked.save(update_fields=["username"])

        self.stdout.write(self.style.SUCCESS(f"Renamed user id={user.pk} to {target!r}."))
