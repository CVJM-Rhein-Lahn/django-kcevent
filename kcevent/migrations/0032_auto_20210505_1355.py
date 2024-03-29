# Generated by Django 3.0.4 on 2021-05-05 13:55

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('kcevent', '0031_auto_20210225_1733'),
    ]

    operations = [
        migrations.AddField(
            model_name='kcperson',
            name='createdTime',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Created on'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='kcperson',
            name='updatedTime',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated on'),
        ),
    ]
