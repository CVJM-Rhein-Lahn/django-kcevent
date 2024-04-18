# Generated by Django 5.0.4 on 2024-04-18 13:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kcevent", "0038_merge_20240418_0745"),
    ]

    operations = [
        migrations.CreateModel(
            name="KCEventExportSetting",
            fields=[
                (
                    "event_id",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="kcevent.kcevent",
                        verbose_name="Event",
                    ),
                ),
                (
                    "sheet_name",
                    models.CharField(max_length=120, verbose_name="Sheet name"),
                ),
                (
                    "folder_id",
                    models.CharField(max_length=120, verbose_name="Drive folder id"),
                ),
                (
                    "tpl_id",
                    models.CharField(max_length=120, verbose_name="Sheet template id"),
                ),
            ],
            options={
                "verbose_name": "Export setting",
                "verbose_name_plural": "Export settings",
            },
        ),
    ]
