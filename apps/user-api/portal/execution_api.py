import shlex
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AuditEvent, ExecutionRecord, ProgrammeMembership


TERMINAL_STATES = {
    ExecutionRecord.State.COMPLETED,
    ExecutionRecord.State.FAILED,
    ExecutionRecord.State.CANCELLED,
}

logger = logging.getLogger(__name__)


class SlurmGatewayHistoryError(RuntimeError):
    """Bounded diagnostic category without leaking privileged SSH output."""

    def __init__(self, reason):
        super().__init__("Scheduler history is temporarily unavailable.")
        self.reason = reason


SLURM_STATE_MAP = {
    "PENDING": ExecutionRecord.State.QUEUED,
    "CONFIGURING": ExecutionRecord.State.QUEUED,
    "RUNNING": ExecutionRecord.State.RUNNING,
    "COMPLETING": ExecutionRecord.State.RUNNING,
    "COMPLETED": ExecutionRecord.State.COMPLETED,
    "CANCELLED": ExecutionRecord.State.CANCELLED,
    "FAILED": ExecutionRecord.State.FAILED,
    "TIMEOUT": ExecutionRecord.State.FAILED,
    "NODE_FAIL": ExecutionRecord.State.FAILED,
    "OUT_OF_MEMORY": ExecutionRecord.State.FAILED,
    "PREEMPTED": ExecutionRecord.State.FAILED,
}


def _audit(actor, event_type, record, metadata=None):
    AuditEvent.objects.create(
        actor=actor,
        event_type=event_type,
        object_type="ExecutionRecord",
        object_id=str(record.pk),
        metadata=metadata or {},
    )


def _entitled(user):
    if user.is_staff or user.is_superuser:
        return True
    person = getattr(user, "person", None)
    if person is None:
        return False
    return ProgrammeMembership.objects.filter(
        person=person,
        status=ProgrammeMembership.Status.APPROVED,
    ).exists()


def _configured():
    return bool(
        settings.SLURM_GATEWAY_HOST
        and settings.QUANTUM_WORKFLOWS_CPU_IMAGE
        and settings.SLURM_GATEWAY_PRIVATE_KEY
        and settings.SLURM_GATEWAY_KNOWN_HOSTS
    )


def _gateway(op, arg, stdin=None):
    with tempfile.TemporaryDirectory(prefix="quantum-slurm-") as directory:
        key_path = Path(directory) / "id_ed25519"
        known_hosts_path = Path(directory) / "known_hosts"
        key_path.write_text(settings.SLURM_GATEWAY_PRIVATE_KEY)
        known_hosts_path.write_text(settings.SLURM_GATEWAY_KNOWN_HOSTS)
        os.chmod(key_path, 0o600)
        os.chmod(known_hosts_path, 0o600)

        command = [
            "ssh",
            "-i",
            str(key_path),
            "-o",
            "BatchMode=yes",
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={known_hosts_path}",
            "-p",
            str(settings.SLURM_GATEWAY_PORT),
            f"{settings.SLURM_GATEWAY_USER}@{settings.SLURM_GATEWAY_HOST}",
            f"{op} {arg}",
        ]
        try:
            result = subprocess.run(
                command,
                input=stdin,
                text=True,
                capture_output=True,
                check=True,
                timeout=20,
            )
        except subprocess.CalledProcessError as exc:
            if op == "history":
                reason = {
                    64: "history_command_not_installed",
                    77: "research_identity_not_entitled",
                    255: "ssh_gateway_unreachable_or_unauthorized",
                }.get(exc.returncode, "scheduler_accounting_command_failed")
                logger.warning("Slurm history gateway failure: %s (exit %s)",
                               reason, exc.returncode)
                raise SlurmGatewayHistoryError(reason) from exc
            message = (
                exc.stderr or exc.stdout or "Slurm gateway command failed."
            ).strip()
            raise RuntimeError(message) from exc
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError("Slurm gateway is unavailable.") from exc
        return result.stdout.strip()


def _cpu_smoke_script(record):
    result_path = record.result_path
    image = settings.QUANTUM_WORKFLOWS_CPU_IMAGE
    home_path = f"/home/research/{record.user.username}"
    log_path = f"{home_path}/.quantum-platform/slurm-%j.out"

    return f"""#!/usr/bin/env bash
#SBATCH --job-name=jhub-cpu-smoke
#SBATCH --partition=cpu-small
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --chdir={shlex.quote(home_path)}
#SBATCH --output={shlex.quote(log_path)}

set -euo pipefail

result_root={shlex.quote(result_path)}
image={shlex.quote(image)}

mkdir -p "$result_root"
srun /usr/bin/apptainer exec \
  --bind "$result_root:/results" \
  "$image" \
  qw cpu-smoke \
    --iterations 100000 \
    --output /results
"""


def _bell_aer_script(record):
    """Fixed, credential-free Bell experiment on the existing Slurm CPU runner."""
    result_path = record.result_path
    image = settings.QUANTUM_WORKFLOWS_CPU_IMAGE
    home_path = f"/home/research/{record.user.username}"
    log_path = f"{home_path}/.quantum-platform/slurm-%j.out"

    return f"""#!/usr/bin/env bash
#SBATCH --job-name=jhub-bell-aer
#SBATCH --partition=cpu-small
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --chdir={shlex.quote(home_path)}
#SBATCH --output={shlex.quote(log_path)}

set -euo pipefail

result_root={shlex.quote(result_path)}
image={shlex.quote(image)}

mkdir -p "$result_root"
srun /usr/bin/apptainer exec \\
  --bind "$result_root:/results" \\
  "$image" \\
  qw hello --executor aer --shots 1024 --seed 42 --output /results
"""


def _payload(record):
    return {
        "id": str(record.pk),
        "offering": record.offering,
        "state": record.state,
        "scheduler_job_id": record.scheduler_job_id or None,
        "scheduler_state": record.scheduler_state or None,
        "scheduler_node": record.scheduler_node or None,
        "parameters": record.parameters,
        "result_path": record.result_path,
        "error_message": record.error_message or None,
        "submitted_at": record.submitted_at,
        "finished_at": record.finished_at,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _refresh(record):
    if not record.scheduler_job_id or record.state in TERMINAL_STATES:
        return record

    output = _gateway("query", record.scheduler_job_id)
    if not output:
        record.state = ExecutionRecord.State.UNKNOWN
        record.scheduler_state = ""
        record.save(update_fields=["state", "scheduler_state", "updated_at"])
        return record

    state, _, node = output.partition("|")
    slurm_state = state.strip().split("+", 1)[0].split(" ", 1)[0]
    record.scheduler_state = slurm_state
    record.scheduler_node = node.strip()
    record.state = SLURM_STATE_MAP.get(slurm_state, ExecutionRecord.State.UNKNOWN)

    if record.state in TERMINAL_STATES:
        record.finished_at = timezone.now()

    record.save(
        update_fields=[
            "scheduler_state",
            "scheduler_node",
            "state",
            "finished_at",
            "updated_at",
        ]
    )
    return record


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def executions(request):
    records = ExecutionRecord.objects.filter(user=request.user)[:50]
    payload = []
    for record in records:
        try:
            record = _refresh(record)
        except RuntimeError:
            pass
        payload.append(_payload(record))
    return Response(payload)


def _submit_fixed_workflow(request, *, offering, parameters, batch_script):
    """Only server-owned templates can be submitted through the restricted gateway."""
    if not _entitled(request.user):
        return Response(
            {"detail": "An approved research programme membership is required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    person = getattr(request.user, "person", None)
    if person is None or person.posix_uid is None or person.posix_gid is None:
        return Response(
            {"detail": "Your POSIX research identity is not provisioned."},
            status=status.HTTP_409_CONFLICT,
        )

    if not _configured():
        return Response(
            {"detail": "The Slurm execution gateway is not configured."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    record = ExecutionRecord.objects.create(
        user=request.user,
        offering=offering,
        state=ExecutionRecord.State.CREATED,
        parameters=parameters,
        result_path="",
    )
    record.result_path = (
        f"/home/research/{request.user.username}/"
        f".quantum-platform/runs/{record.pk}"
    )
    record.save(update_fields=["result_path", "updated_at"])

    try:
        scheduler_job_id = _gateway(
            "submit",
            request.user.username,
            stdin=batch_script(record),
        ).splitlines()[-1].strip()
        if not scheduler_job_id or not scheduler_job_id.split("_", 1)[0].isdigit():
            raise RuntimeError("Slurm gateway returned an invalid job identifier.")
    except RuntimeError as exc:
        record.state = ExecutionRecord.State.FAILED
        record.error_message = str(exc)
        record.finished_at = timezone.now()
        record.save(
            update_fields=["state", "error_message", "finished_at", "updated_at"]
        )
        _audit(request.user, "EXECUTION_SUBMIT_FAILED", record)
        return Response(_payload(record), status=status.HTTP_502_BAD_GATEWAY)

    record.scheduler_job_id = scheduler_job_id
    record.state = ExecutionRecord.State.SUBMITTED
    record.submitted_at = timezone.now()
    record.save(
        update_fields=["scheduler_job_id", "state", "submitted_at", "updated_at"]
    )
    _audit(
        request.user,
        "EXECUTION_SUBMITTED",
        record,
        metadata={"scheduler_job_id": scheduler_job_id},
    )
    return Response(_payload(record), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_cpu_smoke(request):
    return _submit_fixed_workflow(
        request,
        offering="cpu-smoke",
        parameters={"iterations": 100000, "logical_target": "cpu-small"},
        batch_script=_cpu_smoke_script,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_bell_aer(request):
    return _submit_fixed_workflow(
        request,
        offering="bell-aer",
        parameters={
            "shots": 1024,
            "seed": 42,
            "executor": "aer",
            "logical_target": "cpu-small",
        },
        batch_script=_bell_aer_script,
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def slurm_history(request):
    """Read-only scheduler accounting, scoped by signed portal user and POSIX identity.

    Never accept a username, account or job-owner selector from the browser.
    Only the restricted SSH gateway can execute the fixed sacct query; no
    arbitrary commands or output paths are accepted.
    """
    if not _entitled(request.user):
        return Response(
            {"detail": "An approved research programme membership is required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    person = getattr(request.user, "person", None)
    if person is None or person.posix_uid is None or person.posix_gid is None:
        return Response(
            {"detail": "Your POSIX research identity is not provisioned."},
            status=status.HTTP_409_CONFLICT,
        )
    if not _configured():
        return Response(
            {"detail": "The Slurm execution gateway is not configured."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    try:
        # Trust-boundary property: authenticated username only, never request.data
        # or query_params. The gateway verifies that this POSIX user is entitled.
        output = _gateway("history", request.user.username)
    except SlurmGatewayHistoryError as exc:
        return Response(
            {
                "detail": "Scheduler history is temporarily unavailable.",
                "reason": exc.reason,
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except RuntimeError:
        return Response(
            {"detail": "Scheduler history is temporarily unavailable.",
             "reason": "scheduler_gateway_unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    history = []
    for line in output.splitlines()[:75]:
        parts = line.split("|")
        if len(parts) != 10:
            continue
        job, name, partition, state, exit_code, elapsed, submitted, started, finished, nodes = (
            value.strip() for value in parts
        )
        if not job.isdigit():
            continue
        # display data, not a new ExecutionRecord or an assumed job entitlement
        history.append({
            "job_id": job,
            "job_name": name,
            "partition": partition,
            "state": state,
            "exit_code": exit_code,
            "elapsed": elapsed,
            "submitted_at": submitted,
            "started_at": started,
            "finished_at": finished,
            "nodes": nodes,
            "source": "slurm",
        })
    return Response({"items": history, "window_days": 7})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def execution_detail(request, execution_id):
    record = ExecutionRecord.objects.filter(pk=execution_id, user=request.user).first()
    if record is None:
        return Response({"detail": "Execution not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        record = _refresh(record)
    except RuntimeError as exc:
        return Response({**_payload(record), "refresh_error": str(exc)})
    return Response(_payload(record))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_execution(request, execution_id):
    record = ExecutionRecord.objects.filter(pk=execution_id, user=request.user).first()
    if record is None:
        return Response({"detail": "Execution not found."}, status=status.HTTP_404_NOT_FOUND)
    if record.state in TERMINAL_STATES:
        return Response(_payload(record))

    try:
        _gateway("cancel", record.scheduler_job_id)
    except RuntimeError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    record.state = ExecutionRecord.State.CANCELLED
    record.scheduler_state = "CANCELLED"
    record.finished_at = timezone.now()
    record.save(update_fields=["state", "scheduler_state", "finished_at", "updated_at"])
    _audit(request.user, "EXECUTION_CANCELLED", record)
    return Response(_payload(record))
