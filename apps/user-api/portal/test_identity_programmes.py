from django.contrib.auth.models import User
from django.test import TestCase

from .identity import allocate_system_username, username_base
from .models import (
    AgentPrincipal,
    PIApplication,
    Person,
    ProgrammeMembership,
    ResearchProgramme,
)
from .programme_ids import (
    allocate_programme_identifier,
    programme_code,
)
from .programme_services import approve_pi_application_record


class UsernameAllocationTests(TestCase):
    def test_initial_plus_surname(self):
        self.assertEqual(
            username_base("Nyameko", "Lisa"),
            "nlisa",
        )

    def test_collision_suffixes(self):
        User.objects.create_user(
            username="nlisa",
            password="x",
        )
        self.assertEqual(
            allocate_system_username("Nelly", "Lisa"),
            "nlisa1",
        )
        User.objects.create_user(
            username="nlisa1",
            password="x",
        )
        self.assertEqual(
            allocate_system_username("Nigel", "Lisa"),
            "nlisa2",
        )


class ProgrammeIdentifierTests(TestCase):
    def test_requested_qcsc_example(self):
        self.assertEqual(
            programme_code(
                "Hybrid Quantum Centric Supercomputing Workflows"
            ),
            "qcsc",
        )

    def test_full_identifier(self):
        self.assertEqual(
            allocate_programme_identifier(
                "CSIR",
                "nlisa",
                "Hybrid Quantum Centric Supercomputing Workflows",
            ),
            "csir-nlisa-qcsc",
        )


class ProgrammeApprovalTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            "quantum",
            "connect@example.invalid",
            "x",
        )
        self.user = User.objects.create_user(
            "nlisa",
            "nlisa@example.invalid",
            "x",
        )
        self.person = Person.objects.create(
            user=self.user,
            given_names="Nyameko",
            family_name="Lisa",
            preferred_name="Nyameko",
            institution="CSIR",
        )

    def test_approval_materializes_programme_and_pi_membership(self):
        application = PIApplication.objects.create(
            applicant=self.person,
            programme_name=(
                "Hybrid Quantum Centric "
                "Supercomputing Workflows"
            ),
            programme_acronym="csir-nlisa-qcsc",
            programme_description="Research programme",
            institution="CSIR",
        )

        programme, membership = (
            approve_pi_application_record(
                application,
                self.admin,
            )
        )

        self.assertEqual(
            programme.status,
            ResearchProgramme.Status.ACTIVE,
        )
        self.assertEqual(
            programme.acronym,
            "csir-nlisa-qcsc",
        )
        self.assertEqual(
            membership.role,
            ProgrammeMembership.Role.PI,
        )
        self.assertEqual(
            membership.status,
            ProgrammeMembership.Status.APPROVED,
        )

        application.refresh_from_db()
        self.assertEqual(
            application.status,
            PIApplication.Status.APPROVED,
        )

    def test_agent_principal_remains_independent(self):
        principal = AgentPrincipal.objects.create(
            user=self.admin
        )
        self.assertEqual(principal.user, self.admin)
