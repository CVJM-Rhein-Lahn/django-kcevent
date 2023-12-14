# Generated by Django 5.0 on 2023-12-14 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kcevent', '0034_alter_kcevent_id_alter_kceventhost_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='kceventregistration',
            name='confirmation_partner_dt',
            field=models.DateTimeField(null=True, verbose_name='Confirmation date/time'),
        ),
        migrations.AddField(
            model_name='kceventregistration',
            name='confirmation_partner_send',
            field=models.BooleanField(default=False, verbose_name='Confirmation send'),
        ),
        migrations.AddField(
            model_name='participant',
            name='events',
            field=models.ManyToManyField(through='kcevent.KCEventRegistration', to='kcevent.kcevent', verbose_name='Events'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='gender',
            field=models.CharField(choices=[('', 'Please choose your gender'), ('M', 'Male'), ('W', 'Female'), ('D', 'Divert')], max_length=1, verbose_name='Gender'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='nutrition',
            field=models.CharField(blank=True, choices=[('', 'Please choose your nutrition'), ('RGL', 'Regular'), ('VGT', 'Vegetarian'), ('VGN', 'Vegan')], default='', max_length=3, verbose_name='Nutrition'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='role',
            field=models.CharField(choices=[('', 'Please choose your role'), ('CF', 'Confirmand'), ('RL', 'Reloaded'), ('ST', 'Staff')], max_length=2, verbose_name='Role'),
        ),
    ]
