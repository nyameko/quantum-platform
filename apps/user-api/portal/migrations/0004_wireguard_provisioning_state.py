from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0003_agentprincipal"),
    ]

    operations = [
        migrations.AddField(
            model_name="wireguardkey",
            name="assigned_address",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="wireguardkey",
            name="provisioned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
