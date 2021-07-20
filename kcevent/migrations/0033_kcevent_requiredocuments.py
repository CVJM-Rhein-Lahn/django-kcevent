# Generated by Django 3.0.4 on 2021-07-20 18:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kcevent', '0032_auto_20210505_1355'),
    ]

    operations = [
        migrations.AddField(
            model_name='kcevent',
            name='requireDocuments',
            field=models.BooleanField(default=True, help_text='Ask and require certain forms and documents from user to upload.', verbose_name='Require documents'),
        ),
    ]