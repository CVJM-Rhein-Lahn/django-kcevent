# Generated by Django 3.0.2 on 2020-02-02 12:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kcevent', '0014_auto_20200202_1218'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kcevent',
            name='host',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='kcevent.KCEventHost', verbose_name='Host'),
        ),
    ]