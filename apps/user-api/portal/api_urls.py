from django.urls import path

from .identity_api import (
    approve_pi_application,
    create_pi_application,
    institutions,
    list_memberships,
    list_pi_applications,
    list_programmes,
    me,
    reject_pi_application,
    upsert_profile,
)
from .views import (
    approve_membership,
    csrf,
    health,
    list_membership_requests,
    reject_membership,
    request_membership,
)

urlpatterns = [
    path("health/", health, name="health"),
    path("csrf/", csrf, name="csrf"),
    path("institutions/", institutions, name="institutions"),
    path("me/", me, name="me"),
    path("profile/", upsert_profile, name="profile"),
    path("programmes/", list_programmes, name="programmes"),
    path(
        "pi-applications/",
        list_pi_applications,
        name="pi-applications",
    ),
    path(
        "pi-applications/submit/",
        create_pi_application,
        name="pi-application-submit",
    ),
    path(
        "pi-applications/<int:application_id>/approve/",
        approve_pi_application,
        name="pi-application-approve",
    ),
    path(
        "pi-applications/<int:application_id>/reject/",
        reject_pi_application,
        name="pi-application-reject",
    ),
    path("memberships/", list_memberships, name="memberships"),
    path(
        "programmes/<int:programme_id>/membership/",
        request_membership,
        name="programme-membership-request",
    ),
    path(
        "programmes/<int:programme_id>/membership-requests/",
        list_membership_requests,
        name="programme-membership-requests",
    ),
    path(
        "memberships/<int:membership_id>/approve/",
        approve_membership,
        name="membership-approve",
    ),
    path(
        "memberships/<int:membership_id>/reject/",
        reject_membership,
        name="membership-reject",
    ),
]
