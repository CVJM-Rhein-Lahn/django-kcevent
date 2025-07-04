# Generated by Django 5.2 on 2025-07-01 20:07

import django.db.models.deletion
from django.db import migrations, models

def create_statistic_record(apps, schema_editor, row, number, gender, role_name):
    ParticipantRole = apps.get_model("kcevent", "ParticipantRole")
    KCEventPartnerRoleStatistic = apps.get_model("kcevent", "KCEventPartnerRoleStatistic")
    role = ParticipantRole.objects.get(event=row.evp_event, name=role_name)
    if not role:
        return
    
    new = KCEventPartnerRoleStatistic(
        event_partner=row,
        role=role,
        gender=gender,
        apx_participants=number
    )
    new.save()    

def convert_statistic(apps, schema_editor):
    KCEventPartner = apps.get_model("kcevent", "KCEventPartner")
    for row in KCEventPartner.objects.all():
        if row.evp_apx_participant_m > 0:
            create_statistic_record(apps, schema_editor, row, row.evp_apx_participant_m, 'M', 'Confirmand')
        if row.evp_apx_participant_w > 0:
            create_statistic_record(apps, schema_editor, row, row.evp_apx_participant_w, 'W', 'Confirmand')
        if row.evp_apx_participant_d > 0:
            create_statistic_record(apps, schema_editor, row, row.evp_apx_participant_d, 'D', 'Confirmand')
        if row.evp_apx_reloaded_m > 0:
            create_statistic_record(apps, schema_editor, row, row.evp_apx_reloaded_m, 'M', 'Reloaded')
        if row.evp_apx_reloaded_w > 0:
            create_statistic_record(apps, schema_editor, row, row.evp_apx_reloaded_w, 'W', 'Reloaded')
        if row.evp_apx_reloaded_d > 0:
            create_statistic_record(apps, schema_editor, row, row.evp_apx_reloaded_d, 'D', 'Reloaded')
        if row.evp_apx_member_m > 0:
            create_statistic_record(apps, schema_editor, row, row.evp_apx_member_m, 'M', 'Staff')
        if row.evp_apx_member_w > 0:
            create_statistic_record(apps, schema_editor, row, row.evp_apx_member_w, 'W', 'Staff')
        if row.evp_apx_member_d > 0:
            create_statistic_record(apps, schema_editor, row, row.evp_apx_member_d, 'D', 'Staff')    

class Migration(migrations.Migration):

    dependencies = [
        ("kcevent", "0065_alter_kceventregistration_reg_adddata"),
    ]

    operations = [
        migrations.CreateModel(
            name="KCEventPartnerRoleStatistic",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "gender",
                    models.CharField(
                        choices=[
                            (None, "Please choose your gender"),
                            ("M", "Male"),
                            ("W", "Female"),
                            ("D", "Divert"),
                        ],
                        max_length=1,
                        verbose_name="Gender",
                    ),
                ),
                (
                    "apx_participants",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Approx. no. of par."
                    ),
                ),
                (
                    "event_partner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="kcevent.kceventpartner",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="kcevent.participantrole",
                    ),
                ),
            ],
            options={
                "verbose_name": "Partner Role Statistic",
                "verbose_name_plural": "Partner Role Statistics",
                "unique_together": {("role", "event_partner")},
            },
        ),
        migrations.RunPython(convert_statistic, reverse_code=migrations.RunPython.noop),
    ]
