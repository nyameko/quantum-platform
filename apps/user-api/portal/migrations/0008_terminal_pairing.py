# Authenticated browser-approved terminal pairing; no ACP secrets or tokens persisted.
import django.db.models.deletion
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0007_posix_identity_allocator"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TerminalPairing",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("verification_code_sha256", models.CharField(max_length=64, unique=True)),
                ("proof_sha256", models.CharField(max_length=64, unique=True)),
                ("device_label", models.CharField(max_length=80)),
                ("status", models.CharField(
                    choices=[("pending", "Pending browser approval"),
                             ("approved", "Approved"), ("revoked", "Revoked")],
                    default="pending", max_length=16,
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                    related_name="terminal_pairings", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
