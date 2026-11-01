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
        self.assertIn("#SBATCH --chdir=/home/research/nlisa", script)
        self.assertIn("/usr/bin/apptainer exec", script)
        self.assertNotIn("module load apptainer", script)
        self.assertIn("qw cpu-smoke", script)

    @patch("portal.execution_api._gateway", return_value="12346")
    def test_submit_bell_aer_uses_fixed_cpu_slurm_template(self, gateway):
        response = self.client.post(
            "/api/v1/executions/bell-aer/",
            data={"executor": "ibm", "partition": "gpu", "shots": 999999},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        record = ExecutionRecord.objects.get(pk=response.json()["id"])
        self.assertEqual(record.offering, "bell-aer")
        self.assertEqual(record.parameters["logical_target"], "cpu-small")
        self.assertEqual(record.parameters["executor"], "aer")
        self.assertEqual(record.parameters["shots"], 1024)
        self.assertEqual(record.scheduler_job_id, "12346")

        script = gateway.call_args.kwargs["stdin"]
        self.assertIn("#SBATCH --job-name=jhub-bell-aer", script)
        self.assertIn("#SBATCH --time=02:00:00", script)
        self.assertIn("#SBATCH --partition=cpu-small", script)
        self.assertIn("#SBATCH --chdir=/home/research/nlisa", script)
        self.assertIn("/usr/bin/apptainer exec", script)
        self.assertIn("qw hello --executor aer --shots 1024 --seed 42", script)
        self.assertNotIn("--executor ibm", script)
        self.assertNotIn("--gres=gpu", script)
        self.assertIn(str(record.pk), script)

    @patch("portal.execution_api._gateway")
    def test_bell_requires_approved_membership(self, gateway):
        ProgrammeMembership.objects.filter(person=self.person).update(
            status=ProgrammeMembership.Status.SUSPENDED
        )
        response = self.client.post(
            "/api/v1/executions/bell-aer/",
            data={},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403, response.content)
        gateway.assert_not_called()

    @patch("portal.execution_api._gateway")
    def test_bell_requires_provisioned_posix_identity(self, gateway):
        self.person.posix_uid = None
        self.person.save(update_fields=["posix_uid"])
        response = self.client.post(
            "/api/v1/executions/bell-aer/",
            data={},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409, response.content)
        gateway.assert_not_called()

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

    @patch("portal.execution_api._gateway")
    def test_history_is_scoped_to_authenticated_owner_not_browser_query(self, gateway):
        gateway.return_value = (
            "12345|hello-cpu|cpu-small|COMPLETED|0:0|00:00:02|"
            "2026-11-01T22:00:00|2026-11-01T22:00:01|"
            "2026-11-01T22:00:03|slurm-cpu-01\n"
        )
        response = self.client.get(
            "/api/v1/executions/slurm-history/?username=another-user"
        )
        self.assertEqual(response.status_code, 200, response.content)
        gateway.assert_called_once_with("history", "nlisa")
        jobs = response.json()["items"]
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["job_id"], "12345")
        self.assertEqual(jobs[0]["job_name"], "hello-cpu")
        self.assertEqual(jobs[0]["state"], "COMPLETED")

    @patch("portal.execution_api._gateway")
    def test_history_rejects_missing_membership(self, gateway):
        ProgrammeMembership.objects.filter(person=self.person).update(
            status=ProgrammeMembership.Status.SUSPENDED
        )
        response = self.client.get("/api/v1/executions/slurm-history/")
        self.assertEqual(response.status_code, 403)
        gateway.assert_not_called()

    @patch("portal.execution_api._gateway")
    def test_history_rejects_missing_posix_identity(self, gateway):
        self.person.posix_uid = None
        self.person.save(update_fields=["posix_uid"])
        response = self.client.get("/api/v1/executions/slurm-history/")
        self.assertEqual(response.status_code, 409)
        gateway.assert_not_called()

    @patch("portal.execution_api._gateway")
    def test_history_gracefully_reports_uninstalled_gateway(self, gateway):
        gateway.side_effect = RuntimeError("unknown gateway operation")
        response = self.client.get("/api/v1/executions/slurm-history/")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("unknown gateway operation", response.content.decode())

    @patch("portal.execution_api._gateway")
    def test_history_ignores_malformed_or_step_records(self, gateway):
        gateway.return_value = (
            "22.batch|step|cpu-small|COMPLETED|0:0|00:00:01|"
            "2026-11-01T22:00:00|2026-11-01T22:00:01|"
            "2026-11-01T22:00:02|slurm-cpu-01\n"
            "unexpected|format\n"
        )
        response = self.client.get("/api/v1/executions/slurm-history/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["items"], [])

    def test_history_requires_login(self):
        self.client.logout()
        response = self.client.get("/api/v1/executions/slurm-history/")
        self.assertIn(response.status_code, {401, 403})
