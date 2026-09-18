"""Identity and programme API endpoints.

Agent administrator routes and AgentPrincipal deliberately remain in their
existing modules unchanged.
"""

from __future__ import annotations

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from allauth.account.models import EmailAddress

from .constants import (
    INSTITUTION_LABELS,
    institution_payload,
    normalise_institution,
)
from .models import (
    AuditEvent,
    PIApplication,
    Person,
    ProgrammeMembership,
    ResearchProgramme,
)
from .programme_ids import allocate_programme_identifier
from .programme_services import (
    ApprovalError,
    approve_pi_application_record,
    reject_pi_application_record,
)


def _is_platform_admin(user) -> bool:
    return bool(user.is_active and (user.is_staff or user.is_superuser))


def _person_payload(person):
    if person is None:
        return None
    return {
        "id": person.pk,
        "given_names": person.given_names,
        "family_name": person.family_name,
        "preferred_name": person.preferred_name,
        "institution": person.institution,
        "institution_label": INSTITUTION_LABELS.get(
            person.institution,
            person.institution,
        ),
        "orcid": person.orcid,
    }


def _programme_payload(programme):
    return {
        "id": programme.pk,
        "name": programme.name,
        "acronym": programme.acronym,
        "description": programme.description,
        "institution": programme.institution,
        "institution_label": INSTITUTION_LABELS.get(
            programme.institution,
            programme.institution,
        ),
        "status": programme.status,
        "pi": {
            "id": programme.pi_id,
            "name": str(programme.pi),
            "username": programme.pi.user.username,
        },
    }


def _membership_payload(membership):
    return {
        "id": membership.pk,
        "programme": _programme_payload(membership.programme),
        "person": {
            "id": membership.person_id,
            "name": str(membership.person),
            "username": membership.person.user.username,
            "email": membership.person.user.email,
        },
        "role": membership.role,
        "status": membership.status,
        "requested_at": membership.requested_at,
        "approved_at": membership.approved_at,
    }


def _application_payload(application):
    return {
        "id": application.pk,
        "programme_name": application.programme_name,
        "programme_acronym": application.programme_acronym,
        "programme_description": application.programme_description,
        "institution": application.institution,
        "institution_label": INSTITUTION_LABELS.get(
            application.institution,
            application.institution,
        ),
        "status": application.status,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
        "reviewed_at": application.reviewed_at,
        "reviewed_by": application.reviewed_by_id,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def institutions(_request):
    return Response(institution_payload())


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    person = getattr(request.user, "person", None)
    memberships = []
    if person is not None:
        memberships = ProgrammeMembership.objects.filter(
            person=person,
        ).select_related(
            "programme",
            "programme__pi",
            "programme__pi__user",
            "person__user",
        )

    email_verified = EmailAddress.objects.filter(
        user=request.user,
        email__iexact=request.user.email,
        verified=True,
    ).exists()

    return Response(
        {
            "id": request.user.pk,
            "email": request.user.email,
            "username": request.user.username,
            "email_verified": email_verified,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
            "person": _person_payload(person),
            "memberships": [
                _membership_payload(membership)
                for membership in memberships
            ],
        }
    )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def upsert_profile(request):
    given_names = str(request.data.get("given_names", "")).strip()
    family_name = str(request.data.get("family_name", "")).strip()

    if not given_names or not family_name:
        return Response(
            {"detail": "Given names and family name are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        institution = normalise_institution(
            request.data.get("institution", "")
        )
    except ValueError:
        return Response(
            {"detail": "Select a supported primary institution."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    orcid = str(request.data.get("orcid", "")).strip() or None

    person, _ = Person.objects.get_or_create(
        user=request.user,
        defaults={
            "given_names": given_names,
            "family_name": family_name,
        },
    )
    person.given_names = given_names
    person.family_name = family_name
    person.preferred_name = given_names.split()[0]
    person.institution = institution
    person.orcid = orcid
    person.save()

    # Human profile changes deliberately never rename the infrastructure ID.
    request.user.first_name = given_names
    request.user.last_name = family_name
    request.user.save(update_fields=["first_name", "last_name"])

    AuditEvent.objects.create(
        actor=request.user,
        event_type="PROFILE_UPDATED",
        object_type="Person",
        object_id=str(person.pk),
    )
    return Response(_person_payload(person))


@api_view(["GET"])
@permission_classes([AllowAny])
def list_programmes(_request):
    programmes = (
        ResearchProgramme.objects.filter(
            status=ResearchProgramme.Status.ACTIVE
        )
        .select_related("pi", "pi__user")
        .order_by("name")
    )
    return Response(
        [_programme_payload(programme) for programme in programmes]
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_pi_applications(request):
    applications = PIApplication.objects.select_related(
        "applicant",
        "applicant__user",
        "reviewed_by",
    )
    if not _is_platform_admin(request.user):
        person = getattr(request.user, "person", None)
        applications = (
            applications.none()
            if person is None
            else applications.filter(applicant=person)
        )

    return Response(
        [_application_payload(application) for application in applications]
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_pi_application(request):
    programme_name = str(
        request.data.get("programme_name", "")
    ).strip()
    programme_description = str(
        request.data.get("programme_description", "")
    ).strip()

    if not programme_name or not programme_description:
        return Response(
            {"detail": "Programme name and description are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    person = getattr(request.user, "person", None)
    if person is None:
        return Response(
            {"detail": "Complete your research profile first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        institution = normalise_institution(
            request.data.get("institution", person.institution)
        )
    except ValueError:
        return Response(
            {"detail": "Select a supported primary institution."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if ResearchProgramme.objects.filter(
        name__iexact=programme_name
    ).exists():
        return Response(
            {"detail": "A programme with this name already exists."},
            status=status.HTTP_409_CONFLICT,
        )

    if PIApplication.objects.filter(
        applicant=person,
        programme_name__iexact=programme_name,
        status=PIApplication.Status.PENDING,
    ).exists():
        return Response(
            {"detail": "You already have a pending application for this programme."},
            status=status.HTTP_409_CONFLICT,
        )

    with transaction.atomic():
        person.institution = institution
        person.save(update_fields=["institution", "updated_at"])

        acronym = allocate_programme_identifier(
            institution,
            request.user.username,
            programme_name,
        )

        application = PIApplication.objects.create(
            applicant=person,
            programme_name=programme_name,
            programme_acronym=acronym,
            programme_description=programme_description,
            institution=institution,
        )

        AuditEvent.objects.create(
            actor=request.user,
            event_type="PI_APPLICATION_SUBMITTED",
            object_type="PIApplication",
            object_id=str(application.pk),
            metadata={"programme_acronym": acronym},
        )

    return Response(
        _application_payload(application),
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_pi_application(request, application_id):
    if not _is_platform_admin(request.user):
        return Response(
            {"detail": "Administrator access is required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    application = PIApplication.objects.filter(pk=application_id).first()
    if application is None:
        return Response(
            {"detail": "PI application not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        programme, membership = approve_pi_application_record(
            application,
            request.user,
        )
    except ApprovalError as exc:
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_409_CONFLICT,
        )

    application.refresh_from_db()
    return Response(
        {
            "application": _application_payload(application),
            "programme": _programme_payload(programme),
            "membership": _membership_payload(membership),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_pi_application(request, application_id):
    if not _is_platform_admin(request.user):
        return Response(
            {"detail": "Administrator access is required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    application = PIApplication.objects.filter(pk=application_id).first()
    if application is None:
        return Response(
            {"detail": "PI application not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        reject_pi_application_record(application, request.user)
    except ApprovalError as exc:
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_409_CONFLICT,
        )

    application.refresh_from_db()
    return Response(_application_payload(application))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_memberships(request):
    person = getattr(request.user, "person", None)
    if person is None:
        return Response([])

    memberships = (
        ProgrammeMembership.objects.filter(person=person)
        .select_related(
            "programme",
            "programme__pi",
            "programme__pi__user",
            "person__user",
        )
        .order_by("programme__name")
    )
    return Response(
        [_membership_payload(membership) for membership in memberships]
    )
