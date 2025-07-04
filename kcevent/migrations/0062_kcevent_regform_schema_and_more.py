# Generated by Django 5.2 on 2025-06-30 06:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "kcevent",
            "0061_alter_kceventregistration_reg_status_participantrole_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="kcevent",
            name="regform_schema",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Specify a JSON based schema for additional form fields.",
                verbose_name="Additional form data",
            ),
        ),
        migrations.AlterField(
            model_name="kcevent",
            name="enableEmergencyContacts",
            field=models.BooleanField(
                default=False,
                help_text="Ask and require to capture emergency contacts.",
                verbose_name="Ask for emergency contacts",
            ),
        ),
        migrations.AlterField(
            model_name="participant",
            name="role",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="kcevent.participantrole",
                verbose_name="Role",
            ),
        ),
    ]
