from django.urls import path

from .access_keys_api import (
    revoke_ssh_key,
    revoke_wireguard_key,
    ssh_keys,
    wireguard_keys,
)
from .execution_api import (
    cancel_execution,
    execution_detail,
    executions,
    submit_cpu_smoke,
)
from .internal_wireguard_api import (
    acknowledge_wireguard_peers,
    desired_wireguard_peers,
)
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
from .workbench_api import (
    launch_workbench,
    stop_workbench,
    workbench_status,
)
from .views import (
    approve_membership,
    csrf,
    health,
    list_membership_requests,
    logout_session,
    reject_membership,
    request_membership,
)

urlpatterns = [
    path("health/", health, name="health"),
    path("executions/", executions, name="executions"),
    path("executions/cpu-smoke/", submit_cpu_smoke, name="execution-cpu-smoke"),
    path("executions/<uuid:execution_id>/", execution_detail, name="execution-detail"),
    path("executions/<uuid:execution_id>/cancel/", cancel_execution, name="execution-cancel"),
    path(
        "internal/wireguard/peers/",
        desired_wireguard_peers,
        name="internal-wireguard-peers",
    ),
    path(
        "internal/wireguard/reconciled/",
        acknowledge_wireguard_peers,
        name="internal-wireguard-reconciled",
    ),
    path("csrf/", csrf, name="csrf"),
    path("logout/", logout_session, name="logout"),
    path("institutions/", institutions, name="institutions"),
    path("me/", me, name="me"),
    path("profile/", upsert_profile, name="profile"),
    path("ssh-keys/", ssh_keys, name="ssh-keys"),
    path(
        "ssh-keys/<int:key_id>/revoke/",
        revoke_ssh_key,
        name="ssh-key-revoke",
    ),
    path("wireguard-keys/", wireguard_keys, name="wireguard-keys"),
    path("workbench/", workbench_status, name="workbench-status"),
    path("workbench/launch/", launch_workbench, name="workbench-launch"),
    path("workbench/stop/", stop_workbench, name="workbench-stop"),
    path(
        "wireguard-keys/<int:key_id>/revoke/",
        revoke_wireguard_key,
        name="wireguard-key-revoke",
    ),
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
