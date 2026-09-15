from allauth.account.models import EmailAddress
from django.db import connection, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    AuditEvent,
    Person,
    PIApplication,
    ProgrammeMembership,
    ResearchProgramme,
)


def _is_platform_admin(user):
    return user.is_staff or user.is_superuser


def _audit(actor, event_type, obj=None, metadata=None):
    AuditEvent.objects.create(
        actor=actor,
        event_type=event_type,
        object_type=obj.__class__.__name__ if obj else "",
        object_id=str(obj.pk) if obj and obj.pk else "",
        metadata=metadata or {},
    )


def _person_payload(person):
    if not person:
        return None

    return {
        "id": person.id,
        "given_names": person.given_names,
        "family_name": person.family_name,
        "preferred_name": person.preferred_name,
        "institution": person.institution,
        "department": person.department,
        "orcid": person.orcid,
    }


def _programme_payload(programme):
    return {
        "id": programme.id,
        "name": programme.name,
        "acronym": programme.acronym,
        "description": programme.description,
        "institution": programme.institution,
        "status": programme.status,
        "pi": {
            "id": programme.pi.id,
            "name": str(programme.pi),
        },
    }


def _membership_payload(membership):
    return {
        "id": membership.id,
        "programme": {
            "id": membership.programme.id,
            "name": membership.programme.name,
            "acronym": membership.programme.acronym,
        },
        "person": {
            "id": membership.person.id,
            "name": str(membership.person),
            "email": membership.person.user.email,
        },
        "role": membership.role,
        "status": membership.status,
        "requested_at": membership.requested_at,
        "approved_at": membership.approved_at,
    }


def _pi_application_payload(application):
    return {
        "id": application.id,
        "applicant": {
            "id": application.applicant.id,
            "name": str(application.applicant),
            "email": application.applicant.user.email,
        },
        "programme_name": application.programme_name,
        "programme_acronym": application.programme_acronym,
        "programme_description": application.programme_description,
        "institution": application.institution,
        "department": application.department,
        "status": application.status,
        "created_at": application.created_at,
        "reviewed_at": application.reviewed_at,
        "reviewed_by": (
            application.reviewed_by.email
            if application.reviewed_by
            else None
        ),
    }


def _can_review_membership(user, membership):
    if _is_platform_admin(user):
        return True

    return membership.programme.pi.user_id == user.id

def home(request):
    return render(request, "home.html")

@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()

    return Response(
        {
            "status": "ok",
            "service": "quantum-platform-user-api",
            "database": "ok",
        }
    )


@ensure_csrf_cookie
def csrf(_request):
    return JsonResponse({"status": "ok"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    person = getattr(request.user, "person", None)

    verified = EmailAddress.objects.filter(
        user=request.user,
        email__iexact=request.user.email,
        verified=True,
    ).exists()

    memberships = []
    if person:
        memberships = [
            _membership_payload(membership)
            for membership in (
                person.programme_memberships
                .select_related("programme", "person__user")
                .all()
            )
        ]

    return Response(
        {
            "id": request.user.id,
            "email": request.user.email,
            "username": request.user.username,
            "email_verified": verified,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
            "person": _person_payload(person),
            "memberships": memberships,
        }
    )


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def upsert_profile(request):
    person = getattr(request.user, "person", None)

    if person is None:
        required = ("given_names", "family_name")
        missing = [
            field
            for field in required
            if not str(request.data.get(field, "")).strip()
        ]
        if missing:
            return Response(
                {
                    "detail": "Complete the required profile fields.",
                    "fields": missing,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        person = Person.objects.create(
            user=request.user,
            given_names=str(request.data["given_names"]).strip(),
            family_name=str(request.data["family_name"]).strip(),
        )

    for field in (
        "given_names",
        "family_name",
        "preferred_name",
        "institution",
        "department",
    ):
        if field in request.data:
            setattr(
                person,
                field,
                str(request.data.get(field, "")).strip(),
            )

    if "orcid" in request.data:
        orcid = str(request.data.get("orcid", "")).strip()
        person.orcid = orcid or None

    person.save()

    _audit(
        request.user,
        "PROFILE_UPDATED",
        person,
    )

    return Response(_person_payload(person))


@api_view(["GET"])
@permission_classes([AllowAny])
def list_programmes(_request):
    programmes = (
        ResearchProgramme.objects
        .filter(status=ResearchProgramme.Status.ACTIVE)
        .select_related("pi")
    )

    return Response(
        [_programme_payload(programme) for programme in programmes]
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_pi_applications(request):
    applications = (
        PIApplication.objects
        .select_related("applicant__user", "reviewed_by")
    )

    if not _is_platform_admin(request.user):
        applications = applications.filter(
            applicant__user=request.user,
        )

    return Response(
        [
            _pi_application_payload(application)
            for application in applications
        ]
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_pi_application(request):
    required = (
        "given_names",
        "family_name",
        "institution",
        "programme_name",
        "programme_description",
    )

    missing = [
        field
        for field in required
        if not str(request.data.get(field, "")).strip()
    ]

    if missing:
        return Response(
            {
                "detail": "Missing required fields.",
                "fields": missing,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    programme_name = str(request.data["programme_name"]).strip()

    with transaction.atomic():
        person, _created = Person.objects.get_or_create(
            user=request.user,
            defaults={
                "given_names": str(
                    request.data["given_names"]
                ).strip(),
                "family_name": str(
                    request.data["family_name"]
                ).strip(),
                "institution": str(
                    request.data["institution"]
                ).strip(),
            },
        )

        for field in (
            "given_names",
            "family_name",
            "institution",
            "department",
        ):
            if field in request.data:
                setattr(
                    person,
                    field,
                    str(request.data.get(field, "")).strip(),
                )

        if "orcid" in request.data:
            orcid = str(request.data.get("orcid", "")).strip()
            person.orcid = orcid or None

        person.save()

        duplicate = PIApplication.objects.filter(
            applicant=person,
            programme_name__iexact=programme_name,
            status=PIApplication.Status.PENDING,
        ).exists()

        if duplicate:
            return Response(
                {
                    "detail": (
                        "A pending PI application already exists "
                        "for this programme."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        application = PIApplication.objects.create(
            applicant=person,
            programme_name=programme_name,
            programme_acronym=str(
                request.data.get("programme_acronym", "")
            ).strip(),
            programme_description=str(
                request.data["programme_description"]
            ).strip(),
            institution=str(
                request.data["institution"]
            ).strip(),
            department=str(
                request.data.get("department", "")
            ).strip(),
        )

        _audit(
            request.user,
            "PI_APPLICATION_SUBMITTED",
            application,
        )

    return Response(
        _pi_application_payload(application),
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_pi_application(request, application_id):
    if not _is_platform_admin(request.user):
        return Response(
            {"detail": "Platform administrator approval required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    with transaction.atomic():
        application = (
            PIApplication.objects
            .select_for_update()
            .select_related("applicant__user")
            .filter(pk=application_id)
            .first()
        )

        if application is None:
            return Response(
                {"detail": "PI application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.status != PIApplication.Status.PENDING:
            return Response(
                {"detail": "This PI application has already been reviewed."},
                status=status.HTTP_409_CONFLICT,
            )

        if ResearchProgramme.objects.filter(
            name__iexact=application.programme_name,
        ).exists():
            return Response(
                {
                    "detail": (
                        "A research programme with this name "
                        "already exists."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        programme = ResearchProgramme.objects.create(
            name=application.programme_name,
            acronym=application.programme_acronym,
            description=application.programme_description,
            institution=application.institution,
            pi=application.applicant,
            status=ResearchProgramme.Status.ACTIVE,
        )

        membership, _created = (
            ProgrammeMembership.objects.get_or_create(
                programme=programme,
                person=application.applicant,
                defaults={
                    "role": ProgrammeMembership.Role.PI,
                    "status": ProgrammeMembership.Status.APPROVED,
                    "approved_at": timezone.now(),
                },
            )
        )

        membership.role = ProgrammeMembership.Role.PI
        membership.status = ProgrammeMembership.Status.APPROVED
        membership.approved_at = timezone.now()
        membership.save(
            update_fields=["role", "status", "approved_at"]
        )

        application.status = PIApplication.Status.APPROVED
        application.reviewed_at = timezone.now()
        application.reviewed_by = request.user
        application.save(
            update_fields=["status", "reviewed_at", "reviewed_by"]
        )

        _audit(
            request.user,
            "PI_APPLICATION_APPROVED",
            application,
            metadata={"programme_id": programme.id},
        )

    return Response(
        {
            "application": _pi_application_payload(application),
            "programme": _programme_payload(programme),
            "membership": _membership_payload(membership),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_pi_application(request, application_id):
    if not _is_platform_admin(request.user):
        return Response(
            {"detail": "Platform administrator approval required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    with transaction.atomic():
        application = (
            PIApplication.objects
            .select_for_update()
            .select_related("applicant__user")
            .filter(pk=application_id)
            .first()
        )

        if application is None:
            return Response(
                {"detail": "PI application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.status != PIApplication.Status.PENDING:
            return Response(
                {"detail": "This PI application has already been reviewed."},
                status=status.HTTP_409_CONFLICT,
            )

        application.status = PIApplication.Status.REJECTED
        application.reviewed_at = timezone.now()
        application.reviewed_by = request.user
        application.save(
            update_fields=["status", "reviewed_at", "reviewed_by"]
        )

        _audit(
            request.user,
            "PI_APPLICATION_REJECTED",
            application,
        )

    return Response(_pi_application_payload(application))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_memberships(request):
    memberships = (
        ProgrammeMembership.objects
        .filter(person__user=request.user)
        .select_related("programme", "person__user")
    )

    return Response(
        [
            _membership_payload(membership)
            for membership in memberships
        ]
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_membership(request, programme_id):
    programme = (
        ResearchProgramme.objects
        .select_related("pi__user")
        .filter(
            id=programme_id,
            status=ResearchProgramme.Status.ACTIVE,
        )
        .first()
    )

    if programme is None:
        return Response(
            {"detail": "Programme not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    person = getattr(request.user, "person", None)

    if person is None:
        return Response(
            {
                "detail": (
                    "Complete your profile before requesting membership."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    membership, created = ProgrammeMembership.objects.get_or_create(
        programme=programme,
        person=person,
        defaults={
            "role": ProgrammeMembership.Role.RESEARCHER,
            "status": ProgrammeMembership.Status.PENDING,
        },
    )

    if not created:
        if membership.status == ProgrammeMembership.Status.APPROVED:
            return Response(
                {"detail": "You are already an approved member."},
                status=status.HTTP_409_CONFLICT,
            )

        if membership.status == ProgrammeMembership.Status.SUSPENDED:
            return Response(
                {"detail": "This membership is suspended."},
                status=status.HTTP_409_CONFLICT,
            )

        membership.role = ProgrammeMembership.Role.RESEARCHER
        membership.status = ProgrammeMembership.Status.PENDING
        membership.requested_at = timezone.now()
        membership.approved_at = None
        membership.save(
            update_fields=[
                "role",
                "status",
                "requested_at",
                "approved_at",
            ]
        )

    _audit(
        request.user,
        "MEMBERSHIP_REQUESTED",
        membership,
        metadata={"programme_id": programme.id},
    )

    return Response(
        _membership_payload(membership),
        status=(
            status.HTTP_201_CREATED
            if created
            else status.HTTP_200_OK
        ),
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_membership_requests(request, programme_id):
    programme = (
        ResearchProgramme.objects
        .select_related("pi__user")
        .filter(pk=programme_id)
        .first()
    )

    if programme is None:
        return Response(
            {"detail": "Programme not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if (
        not _is_platform_admin(request.user)
        and programme.pi.user_id != request.user.id
    ):
        return Response(
            {"detail": "Programme PI approval required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    memberships = (
        ProgrammeMembership.objects
        .filter(
            programme=programme,
            status=ProgrammeMembership.Status.PENDING,
        )
        .select_related("programme", "person__user")
    )

    return Response(
        [
            _membership_payload(membership)
            for membership in memberships
        ]
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_membership(request, membership_id):
    with transaction.atomic():
        membership = (
            ProgrammeMembership.objects
            .select_for_update()
            .select_related("programme__pi__user", "person__user")
            .filter(pk=membership_id)
            .first()
        )

        if membership is None:
            return Response(
                {"detail": "Membership request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not _can_review_membership(request.user, membership):
            return Response(
                {"detail": "Programme PI approval required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if membership.status != ProgrammeMembership.Status.PENDING:
            return Response(
                {"detail": "This membership request is not pending."},
                status=status.HTTP_409_CONFLICT,
            )

        membership.status = ProgrammeMembership.Status.APPROVED
        membership.approved_at = timezone.now()
        membership.save(
            update_fields=["status", "approved_at"]
        )

        _audit(
            request.user,
            "MEMBERSHIP_APPROVED",
            membership,
            metadata={
                "programme_id": membership.programme_id,
                "person_id": membership.person_id,
            },
        )

    return Response(_membership_payload(membership))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_membership(request, membership_id):
    with transaction.atomic():
        membership = (
            ProgrammeMembership.objects
            .select_for_update()
            .select_related("programme__pi__user", "person__user")
            .filter(pk=membership_id)
            .first()
        )

        if membership is None:
            return Response(
                {"detail": "Membership request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not _can_review_membership(request.user, membership):
            return Response(
                {"detail": "Programme PI approval required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if membership.status != ProgrammeMembership.Status.PENDING:
            return Response(
                {"detail": "This membership request is not pending."},
                status=status.HTTP_409_CONFLICT,
            )

        membership.status = ProgrammeMembership.Status.REJECTED
        membership.approved_at = None
        membership.save(
            update_fields=["status", "approved_at"]
        )

        _audit(
            request.user,
            "MEMBERSHIP_REJECTED",
            membership,
            metadata={
                "programme_id": membership.programme_id,
                "person_id": membership.person_id,
            },
        )

    return Response(_membership_payload(membership))
