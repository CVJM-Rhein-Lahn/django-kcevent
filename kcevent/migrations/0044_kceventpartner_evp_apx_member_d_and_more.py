# Generated by Django 5.1 on 2024-08-31 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kcevent", "0043_kceventlocation_kceventhost_address_line_2_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="kceventpartner",
            name="evp_apx_member_d",
            field=models.PositiveSmallIntegerField(
                default=0, verbose_name="Approx. no. of diverse members"
            ),
        ),
        migrations.AddField(
            model_name="kceventpartner",
            name="evp_apx_participant_d",
            field=models.PositiveSmallIntegerField(
                default=0, verbose_name="Approx. no. of diverse par."
            ),
        ),
        migrations.AddField(
            model_name="kceventpartner",
            name="evp_apx_reloaded_d",
            field=models.PositiveSmallIntegerField(
                default=0, verbose_name="Approx. no. of diverse reloaded"
            ),
        ),
    ]
