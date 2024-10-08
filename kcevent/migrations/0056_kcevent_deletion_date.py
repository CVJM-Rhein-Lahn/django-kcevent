# Generated by Django 5.1 on 2024-09-05 04:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kcevent", "0055_partneruser"),
    ]

    operations = [
        migrations.AddField(
            model_name="kcevent",
            name="deletion_date",
            field=models.DateField(
                blank=True,
                help_text="Date at which the event should be deleted with all its related data to comply to the data protection policy. If no date is specified the event will not be deleted automatically.",
                null=True,
                verbose_name="Deletion date",
            ),
        ),
    ]
