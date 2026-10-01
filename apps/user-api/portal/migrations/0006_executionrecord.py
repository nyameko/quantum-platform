import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0005_person_posix_identity"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ExecutionRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("offering", models.CharField(max_length=64)),
                ("state", models.CharField(choices=[("created", "Created"), ("submitted", "Submitted"), ("queued", "Queued"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed"), ("cancelled", "Cancelled"), ("unknown", "Unknown")], default="created", max_length=16)),
                ("scheduler_job_id", models.CharField(blank=True, max_length=64)),
                ("scheduler_state", models.CharField(blank=True, max_length=64)),
                ("scheduler_node", models.CharField(blank=True, max_length=255)),
                ("parameters", models.JSONField(blank=True, default=dict)),
                ("result_path", models.CharField(max_length=512)),
                ("error_message", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="execution_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
