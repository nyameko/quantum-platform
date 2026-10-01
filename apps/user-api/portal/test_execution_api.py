from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from portal.models import ExecutionRecord, Person, ProgrammeMembership, ResearchProgramme


@override_settings(
    SLURM_GATEWAY_HOST="slurm-login.internal",
    SLURM_GATEWAY_PRIVATE_KEY="test-private-key",
    SLURM_GATEWAY_KNOWN_HOSTS="slurm-login.internal test-host-key",
    QUANTUM_WORKFLOWS_CPU_IMAGE="/var/cache/quantum-platform/containers/qw.sif",
)
class ExecutionApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="nlisa",
            email="nlisa@example.invalid",
            password="test-password",
        )
        self.person = Person.objects.create(
            user=self.user,
            given_names="Nyameko Lisa",
            family_name="Researcher",
            institution="CSIR",
            posix_uid=20999,
            posix_gid=20999,
        )
        programme = ResearchProgramme.objects.create(
            name="Test Programme",
            acronym="TEST",
            description="Test",
            institution="CSIR",
            pi=self.person,
            status=ResearchProgramme.Status.ACTIVE,
        )
        ProgrammeMembership.objects.create(
            programme=programme,
            person=self.person,
            role=ProgrammeMembership.Role.PI,
            status=ProgrammeMembership.Status.APPROVED,
        )
        self.client.force_login(self.user)

    @patch("portal.execution_api._gateway", return_value="12345")
    def test_submit_cpu_smoke_creates_durable_execution(self, gateway):
        response = self.client.post(
            "/api/v1/executions/cpu-smoke/",
            data={},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        record = ExecutionRecord.objects.get(pk=response.json()["id"])
        self.assertEqual(record.scheduler_job_id, "12345")
        self.assertEqual(record.state, ExecutionRecord.State.SUBMITTED)
        script = gateway.call_args.kwargs["stdin"]
        self.assertIn("#SBATCH --job-name=jhub-cpu-smoke", script)
        self.assertIn("qw cpu-smoke", script)

    @patch("portal.execution_api.Path.exists", return_value=True)
    @patch("portal.execution_api._gateway", return_value="COMPLETED|slurm-cpu-01")
    def test_detail_refreshes_completed_slurm_state(self, _gateway, _path_exists):
        record = ExecutionRecord.objects.create(
            user=self.user,
            offering="cpu-smoke",
            state=ExecutionRecord.State.SUBMITTED,
            scheduler_job_id="12345",
            result_path="/home/research/nlisa/result",
        )
        response = self.client.get(f"/api/v1/executions/{record.pk}/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["state"], "completed")
        self.assertEqual(response.json()["scheduler_node"], "slurm-cpu-01")
