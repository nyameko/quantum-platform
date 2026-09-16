from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Gauge,
    generate_latest,
)

from .models import (
    AuditEvent,
    Person,
    PIApplication,
    ProgrammeMembership,
    ResearchProgramme,
    SSHKey,
    WireGuardKey,
)


def metrics(request):
    registry = CollectorRegistry()

    Gauge(
        "quantum_platform_users_total",
        "Registered Django users.",
        registry=registry,
    ).set(User.objects.count())

    Gauge(
        "quantum_platform_people_total",
        "Researcher profiles.",
        registry=registry,
    ).set(Person.objects.count())

    programmes = Gauge(
        "quantum_platform_research_programmes",
        "Research programmes by status.",
        ["status"],
        registry=registry,
    )

    for status, _ in ResearchProgramme.Status.choices:
        programmes.labels(status=status).set(
            ResearchProgramme.objects.filter(status=status).count()
        )

    memberships = Gauge(
        "quantum_platform_programme_memberships",
        "Programme memberships by status and role.",
        ["status", "role"],
        registry=registry,
    )

    for status, _ in ProgrammeMembership.Status.choices:
        for role, _ in ProgrammeMembership.Role.choices:
            memberships.labels(
                status=status,
                role=role,
            ).set(
                ProgrammeMembership.objects.filter(
                    status=status,
                    role=role,
                ).count()
            )

    pi_applications = Gauge(
        "quantum_platform_pi_applications",
        "PI applications by status.",
        ["status"],
        registry=registry,
    )

    for status, _ in PIApplication.Status.choices:
        pi_applications.labels(status=status).set(
            PIApplication.objects.filter(status=status).count()
        )

    ssh_keys = Gauge(
        "quantum_platform_ssh_keys",
        "SSH keys by active state.",
        ["active"],
        registry=registry,
    )

    wireguard_keys = Gauge(
        "quantum_platform_wireguard_keys",
        "WireGuard keys by active state.",
        ["active"],
        registry=registry,
    )

    for active in (True, False):
        active_label = str(active).lower()

        ssh_keys.labels(active=active_label).set(
            SSHKey.objects.filter(active=active).count()
        )

        wireguard_keys.labels(active=active_label).set(
            WireGuardKey.objects.filter(active=active).count()
        )

    audit_events = Gauge(
        "quantum_platform_audit_events",
        "Audit events grouped by type.",
        ["event_type"],
        registry=registry,
    )

    for row in (
        AuditEvent.objects.values("event_type")
        .annotate(total=Count("id"))
        .order_by()
    ):
        audit_events.labels(
            event_type=row["event_type"]
        ).set(row["total"])

    return HttpResponse(
        generate_latest(registry),
        content_type=CONTENT_TYPE_LATEST,
    )
