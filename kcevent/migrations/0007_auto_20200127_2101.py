# Generated by Django 3.0.2 on 2020-01-27 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kcevent', '0006_kceventregistration_reg_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kceventregistration',
            name='reg_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
