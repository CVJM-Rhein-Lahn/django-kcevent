# Generated by Django 5.1 on 2024-10-20 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kcevent", "0056_kcevent_deletion_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="kcevent",
            name="enablePrices",
            field=models.BooleanField(
                default=False,
                help_text="Calculate and show of price information in event registration based on defined rules.",
                verbose_name="Enable Prices",
            ),
        ),
    ]
