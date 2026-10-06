from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portal.identity import allocate_posix_identity


class Command(BaseCommand):
    help = "Allocate a never-reused Quantum Platform POSIX UID/GID for a user."

    def add_arguments(self, parser):
        parser.add_argument("username")

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]

        try:
            user = User.objects.select_for_update().get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"Unknown user: {username}") from exc

        person = getattr(user, "person", None)
        if person is None:
            raise CommandError(
                f"User {username} does not have a research Person profile."
            )

        uid, gid = allocate_posix_identity(person)
        self.stdout.write(f"{username} {uid}:{gid}")
