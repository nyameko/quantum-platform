from django.db import migrations, models
import django.db.models.deletion


def seed_research_sequence(apps, schema_editor):
    Sequence = apps.get_model("portal", "PosixIdentitySequence")
    Sequence.objects.update_or_create(
        name="research",
        defaults={"next_uid": 21000},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0006_executionrecord"),
    ]

    operations = [
        migrations.CreateModel(
            name="PosixIdentitySequence",
            fields=[
                ("name", models.CharField(max_length=32, primary_key=True, serialize=False)),
                ("next_uid", models.PositiveIntegerField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="PosixIdentityAllocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uid", models.PositiveIntegerField(unique=True)),
                ("gid", models.PositiveIntegerField(unique=True)),
                ("username", models.CharField(max_length=150)),
                ("allocated_at", models.DateTimeField(auto_now_add=True)),
                ("person", models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="posix_identity_allocation",
                    to="portal.person",
                )),
            ],
            options={"ordering": ["uid"]},
        ),
        migrations.RunPython(seed_research_sequence, migrations.RunPython.noop),
    ]
}
