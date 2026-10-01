from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0004_wireguard_provisioning_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="posix_uid",
            field=models.PositiveIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="person",
            name="posix_gid",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="person",
            name="posix_provisioned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
