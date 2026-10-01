import shlex
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
    log_path = f"/home/research/{record.user.username}/.quantum-platform/slurm-%j.out"

    return f"""#!/usr/bin/env bash
#SBATCH --job-name=jhub-cpu-smoke
#SBATCH --partition=cpu-small
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output={shlex.quote(log_path)}

set -euo pipefail

result_root={shlex.quote(result_path)}
image={shlex.quote(image)}

mkdir -p "$result_root"
module load apptainer
srun apptainer exec \
  --bind "$result_root:/results" \
  "$image" \
  qw cpu-smoke \
    --iterations 100000 \
    --output /results
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_cpu_smoke(request):
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
        offering="cpu-smoke",
        state=ExecutionRecord.State.CREATED,
        parameters={"iterations": 100000, "logical_target": "cpu-small"},
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
            stdin=_cpu_smoke_script(record),
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
