# Generated by Django 3.0.2 on 2020-02-02 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kcevent', '0017_auto_20200202_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kctemplate',
            name='tpl_content',
            field=models.TextField(verbose_name='Body template'),
        ),
        migrations.AlterField(
            model_name='kctemplate',
            name='tpl_subject',
            field=models.CharField(max_length=255, verbose_name='Subject template'),
        ),
    ]
