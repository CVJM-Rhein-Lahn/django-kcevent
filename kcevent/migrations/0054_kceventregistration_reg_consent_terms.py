# Generated by Django 5.1 on 2024-09-01 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kcevent", "0053_alter_kceventpartner_evp_doc_contract_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="kceventregistration",
            name="reg_consent_terms",
            field=models.BooleanField(
                default=False, verbose_name="Consent to General Terms and Conditions"
            ),
        ),
    ]
