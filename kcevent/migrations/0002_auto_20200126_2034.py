# Generated by Django 3.0.2 on 2020-01-26 20:34

from django.db import migrations, models
import kcevent.models


class Migration(migrations.Migration):

    dependencies = [
        ('kcevent', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kceventpartner',
            name='evp_doc_contract',
            field=models.FileField(null=True, upload_to=kcevent.models.getUploadPathEventPartnerContract),
        ),
    ]
