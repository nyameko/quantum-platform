from django.core.management.base import BaseCommand

from portal.models import PIApplication, ResearchProgramme
from portal.programme_services import (
    ApprovalError,
    reconcile_approved_application,
)


class Command(BaseCommand):
    help = (
        "Find approved PI applications missing programme/PI-membership "
        "side effects. Dry-run unless --apply is supplied."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Create the missing programme/membership records.",
        )

    def handle(self, *args, **options):
        candidates = PIApplication.objects.filter(
            status=PIApplication.Status.APPROVED
        ).select_related("applicant__user")

        orphaned = [
            application
            for application in candidates
            if not ResearchProgramme.objects.filter(
                name__iexact=application.programme_name
            ).exists()
        ]

        if not orphaned:
            self.stdout.write(
                self.style.SUCCESS(
                    "No orphaned approved PI applications."
                )
            )
            return

        for application in orphaned:
            self.stdout.write(
                f"{application.pk}: "
                f"{application.applicant.user.username} -> "
                f"{application.programme_name!r}"
            )

        if not options["apply"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {len(orphaned)} application(s) need "
                    "reconciliation. Run again with --apply."
                )
            )
            return

        repaired = 0
        for application in orphaned:
            try:
                programme, _membership = (
                    reconcile_approved_application(application)
                )
            except ApprovalError as exc:
                self.stderr.write(
                    self.style.ERROR(
                        f"{application.pk}: {exc}"
                    )
                )
                continue

            repaired += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Reconciled {application.pk} -> "
                    f"{programme.acronym}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciled {repaired} application(s)."
            )
        )
