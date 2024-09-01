# Generated by Django 5.0.4 on 2024-04-29 19:13

import django.db.models.deletion
from django.db import migrations, models

MIGRATION_HOST_MAPPING = {}

def migrate_kceventhost(apps, schema_editor):
    global MIGRATION_HOST_MAPPING
    KCEventHost = apps.get_model("kcevent", "KCEventHost")
    Partner = apps.get_model("kcevent", "Partner")
    MIGRATION_HOST_MAPPING = {}
    for host in KCEventHost.objects.all():
        # check if partner with name already exist...
        p = None
        try:
            p = Partner.objects.get(
                name=host.name, 
                street=host.street,
                house_number=host.house_number,
                city=host.city,
                zip_code=host.zip_code,
                mail_addr=host.mail_addr
            )
            p.website = host.website
            p.save()
        except Partner.DoesNotExist:
            p = Partner.objects.create(
                name=host.name, 
                street=host.street,
                house_number=host.house_number,
                city=host.city,
                zip_code=host.zip_code,
                mail_addr=host.mail_addr,
                website=host.website,
                representative=None,
                contact_person=None
            )
        MIGRATION_HOST_MAPPING[str(host.id)] = p.id

def apply_mapping(apps, schema_editor):
    global MIGRATION_HOST_MAPPING
    KCEvent = apps.get_model("kcevent", "KCEvent")
    Partner = apps.get_model("kcevent", "Partner")
    for event in KCEvent.objects.all():
        newId = MIGRATION_HOST_MAPPING[str(event.host_old.id)]
        event.host = Partner.objects.get(id=newId)
        event.save()

class Migration(migrations.Migration):

    dependencies = [
        ("kcevent", "0040_partner_website"),
    ]

    operations = [
        migrations.AlterField(
            model_name="partner",
            name="contact_person",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="kcevent.kcperson",
                verbose_name="Contact person",
            ),
        ),
        migrations.AlterField(
            model_name="partner",
            name="representative",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="kcevent.kcperson",
                verbose_name="Responsible person",
            ),
        ),
        migrations.RunPython(migrate_kceventhost),
        migrations.AddField(
            model_name="kcevent",
            name="partners",
            field=models.ManyToManyField(
                through="kcevent.KCEventPartner",
                to="kcevent.partner",
                verbose_name="Partners",
            ),
        ),
        migrations.RenameField(
            model_name="kcevent",
            old_name="host",
            new_name="host_old"
        ),
        migrations.AddField(
            model_name="kcevent",
            name="host",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="kcevent.partner",
                verbose_name="Host",
            ),
        ),
        migrations.RunPython(apply_mapping),
        migrations.RemoveField(model_name='kcevent', name='host_old')
    ]
