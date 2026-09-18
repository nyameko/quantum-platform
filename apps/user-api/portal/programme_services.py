"""PI-application approval services shared by API and Django Admin."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from .models import (
    AuditEvent,
    PIApplication,
    ProgrammeMembership,
    ResearchProgramme,
)
from .programme_ids import allocate_programme_identifier


class ApprovalError(Exception):
    pass


def _ensure_pi_membership(programme, person):
    membership, _ = ProgrammeMembership.objects.get_or_create(
        programme=programme,
        person=person,
        defaults={
            "role": ProgrammeMembership.Role.PI,
            "status": ProgrammeMembership.Status.APPROVED,
            "approved_at": timezone.now(),
        },
    )

    changed = False
    if membership.role != ProgrammeMembership.Role.PI:
        membership.role = ProgrammeMembership.Role.PI
        changed = True
    if membership.status != ProgrammeMembership.Status.APPROVED:
        membership.status = ProgrammeMembership.Status.APPROVED
        changed = True
    if membership.approved_at is None:
        membership.approved_at = timezone.now()
        changed = True

    if changed:
        membership.save(
            update_fields=["role", "status", "approved_at"],
        )

    return membership


@transaction.atomic
def approve_pi_application_record(application: PIApplication, reviewer):
    application = (
        PIApplication.objects.select_for_update()
        .select_related("applicant__user")
        .get(pk=application.pk)
    )

    if application.status != PIApplication.Status.PENDING:
        raise ApprovalError("This PI application has already been reviewed.")

    if ResearchProgramme.objects.filter(
        name__iexact=application.programme_name
    ).exists():
        raise ApprovalError(
            "A research programme with this name already exists."
        )

    acronym = allocate_programme_identifier(
        application.institution,
        application.applicant.user.username,
        application.programme_name,
        exclude_application_id=application.pk,
    )
    application.programme_acronym = acronym

    programme = ResearchProgramme.objects.create(
        name=application.programme_name,
        acronym=acronym,
        description=application.programme_description,
        institution=application.institution,
        pi=application.applicant,
        status=ResearchProgramme.Status.ACTIVE,
    )

    membership = _ensure_pi_membership(
        programme,
        application.applicant,
    )

    application.status = PIApplication.Status.APPROVED
    application.reviewed_at = timezone.now()
    application.reviewed_by = reviewer
    application.save(
        update_fields=[
            "programme_acronym",
            "status",
            "reviewed_at",
            "reviewed_by",
            "updated_at",
        ],
    )

    AuditEvent.objects.create(
        actor=reviewer,
        event_type="PI_APPLICATION_APPROVED",
        object_type="PIApplication",
        object_id=str(application.pk),
        metadata={
            "programme_id": programme.pk,
            "programme_acronym": programme.acronym,
        },
    )
    return programme, membership


@transaction.atomic
def reject_pi_application_record(application: PIApplication, reviewer):
    application = PIApplication.objects.select_for_update().get(
        pk=application.pk
    )

    if application.status != PIApplication.Status.PENDING:
        raise ApprovalError("This PI application has already been reviewed.")

    application.status = PIApplication.Status.REJECTED
    application.reviewed_at = timezone.now()
    application.reviewed_by = reviewer
    application.save(
        update_fields=[
            "status",
            "reviewed_at",
            "reviewed_by",
            "updated_at",
        ],
    )

    AuditEvent.objects.create(
        actor=reviewer,
        event_type="PI_APPLICATION_REJECTED",
        object_type="PIApplication",
        object_id=str(application.pk),
    )
    return application


@transaction.atomic
def reconcile_approved_application(application: PIApplication, actor=None):
    application = (
        PIApplication.objects.select_for_update()
        .select_related("applicant__user")
        .get(pk=application.pk)
    )

    if application.status != PIApplication.Status.APPROVED:
        raise ApprovalError("Only approved applications can be reconciled.")

    programme = ResearchProgramme.objects.filter(
        name__iexact=application.programme_name
    ).first()

    if programme is None:
        acronym = allocate_programme_identifier(
            application.institution,
            application.applicant.user.username,
            application.programme_name,
            exclude_application_id=application.pk,
        )
        programme = ResearchProgramme.objects.create(
            name=application.programme_name,
            acronym=acronym,
            description=application.programme_description,
            institution=application.institution,
            pi=application.applicant,
            status=ResearchProgramme.Status.ACTIVE,
        )
        application.programme_acronym = acronym
        application.save(
            update_fields=["programme_acronym", "updated_at"],
        )

    membership = _ensure_pi_membership(
        programme,
        application.applicant,
    )

    AuditEvent.objects.create(
        actor=actor,
        event_type="PI_APPLICATION_RECONCILED",
        object_type="PIApplication",
        object_id=str(application.pk),
        metadata={
            "programme_id": programme.pk,
            "programme_acronym": programme.acronym,
        },
    )
    return programme, membership
