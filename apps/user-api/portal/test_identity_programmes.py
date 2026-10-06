from django.contrib.auth.models import User
from django.test import TestCase

from .identity import (
    allocate_posix_identity,
    allocate_system_username,
    username_base,
)
from .models import (
    AgentPrincipal,
    PIApplication,
    Person,
    PosixIdentityAllocation,
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




class PosixIdentityAllocationTests(TestCase):
    def _person(self, username):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.invalid",
            password="x",
        )
        return Person.objects.create(
            user=user,
            given_names=username,
            family_name="Researcher",
            preferred_name=username,
            institution="CSIR",
        )

    def test_first_managed_identity_starts_at_21000(self):
        person = self._person("researcher1")

        uid, gid = allocate_posix_identity(person)

        self.assertEqual((uid, gid), (21000, 21000))
        person.refresh_from_db()
        self.assertEqual(person.posix_uid, 21000)
        self.assertEqual(person.posix_gid, 21000)

    def test_allocator_is_idempotent_for_same_person(self):
        person = self._person("researcher1")

        first = allocate_posix_identity(person)
        second = allocate_posix_identity(person)

        self.assertEqual(first, (21000, 21000))
        self.assertEqual(second, first)
        self.assertEqual(PosixIdentityAllocation.objects.count(), 1)

    def test_allocator_advances_monotonically(self):
        first = self._person("researcher1")
        second = self._person("researcher2")

        self.assertEqual(allocate_posix_identity(first), (21000, 21000))
        self.assertEqual(allocate_posix_identity(second), (21001, 21001))

    def test_deleted_identity_is_never_reused(self):
        first = self._person("researcher1")
        self.assertEqual(allocate_posix_identity(first), (21000, 21000))

        first.user.delete()

        allocation = PosixIdentityAllocation.objects.get(uid=21000)
        self.assertIsNone(allocation.person)

        second = self._person("researcher2")
        self.assertEqual(allocate_posix_identity(second), (21001, 21001))

    def test_existing_bootstrap_identity_does_not_consume_managed_sequence(self):
        bootstrap = self._person("nlisa")
        bootstrap.posix_uid = 20999
        bootstrap.posix_gid = 20999
        bootstrap.save(update_fields=["posix_uid", "posix_gid"])

        self.assertEqual(
            allocate_posix_identity(bootstrap),
            (20999, 20999),
        )

        managed = self._person("researcher1")
        self.assertEqual(allocate_posix_identity(managed), (21000, 21000))


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

        self.person.refresh_from_db()
        self.assertEqual(self.person.posix_uid, 21000)
        self.assertEqual(self.person.posix_gid, 21000)

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
