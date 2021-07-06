# Generated by Django 3.0.4 on 2021-02-20 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kcevent', '0025_auto_20210220_1214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='nutrition',
            field=models.CharField(blank=True, choices=[('RGL', 'Regular'), ('VGT', 'Vegetarian'), ('VGN', 'Vegan')], default='', max_length=3),
        ),
    ]