# Generated by Django 3.0.4 on 2021-02-20 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kcevent', '0024_auto_20210220_1202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='celiac_disease',
            field=models.BooleanField(default=False, verbose_name='Celiac disease'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='intolerances',
            field=models.TextField(blank=True, default='', verbose_name='Intolerances'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='lactose_intolerance',
            field=models.BooleanField(default=False, verbose_name='Lactose intolerance'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='nutrition',
            field=models.CharField(choices=[('RGL', 'Regular'), ('VGT', 'Vegetarian'), ('VGN', 'Vegan')], default=None, max_length=3, null=True),
        ),
    ]
