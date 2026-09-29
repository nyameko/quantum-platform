import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Create or reconcile the one platform administrator. Dry-run by default."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=os.getenv("QUANTUM_PLATFORM_BOOTSTRAP_ADMIN_USERNAME", ""),
        )
        parser.add_argument(
            "--email",
            default=os.getenv("QUANTUM_PLATFORM_BOOTSTRAP_ADMIN_EMAIL", ""),
        )
        parser.add_argument(
            "--password",
            default=os.getenv("QUANTUM_PLATFORM_BOOTSTRAP_ADMIN_PASSWORD", ""),
        )
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        username = options["username"].strip()
        email = options["email"].strip()
        password = options["password"]

        if not username or not email:
            raise CommandError("Bootstrap administrator username and email are required.")

        User = get_user_model()
        user = User.objects.filter(username=username).first()
        created = user is None

        if user is None:
            user = User(username=username, email=email)

        self.stdout.write(f"username={username!r}")
        self.stdout.write(f"email={email!r}")
        self.stdout.write(f"existing={not created}")
        self.stdout.write("desired=is_active,is_staff,is_superuser")

        if not options["apply"]:
            self.stdout.write(self.style.WARNING("DRY RUN: no changes made. Re-run with --apply."))
            return

        with transaction.atomic():
            if not created:
                user = User.objects.select_for_update().get(pk=user.pk)
            user.email = email
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            if password:
                user.set_password(password)
            elif created:
                user.set_unusable_password()
            user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Created' if created else 'Updated'} platform administrator {username!r}."
            )
        )
