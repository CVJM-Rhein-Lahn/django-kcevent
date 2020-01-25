from django.db import models
from django.core import mail

class KCPerson(models.Model):

    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    street = models.CharField(max_length=120)
    house_number = models.CharField(max_length=10)
    city = models.CharField(max_length=120)
    zip_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=50)
    mail_addr = models.EmailField()

class Participant(KCPerson):

    NUTRITION_REGULAR = 'RGL'
    NUTRITION_VEGETARIAN = 'VGT'
    NUTRITION_VEGAN = 'VGN'
    NUTRITION_CHOICES = [
        (NUTRITION_REGULAR, 'Regulär'),
        (NUTRITION_VEGETARIAN, 'Vegetarisch'),
        (NUTRITION_VEGAN, 'Vegan'),
    ]

    ROLE_CONFIRMEE = 'CF'
    ROLE_RELOADED = 'RL'
    ROLE_STAFF = 'ST'
    ROLE_CHOICES = [
        (ROLE_CONFIRMEE, 'Konfirmand'),
        (ROLE_RELOADED, 'Reloaded'),
        (ROLE_STAFF, 'Mitarbeiter')
    ]

    birthday = models.DateField()
    church = models.ForeignKey('Partner', null=True, on_delete=models.SET_NULL)
    intolerances = models.TextField()
    nutrition = models.CharField(
        max_length=3,
        choices=NUTRITION_CHOICES,
        default=NUTRITION_REGULAR,
    )
    role = models.CharField(
        max_length=2,
        choices=ROLE_CHOICES,
        default=ROLE_CONFIRMEE,
    )

class Partner(models.Model):
    name = models.CharField(max_length=250)
    street = models.CharField(max_length=120)
    house_number = models.CharField(max_length=10)
    city = models.CharField(max_length=120)
    zip_code = models.CharField(max_length=10)
    mail_church = models.EmailField()

    representative = models.ForeignKey(KCPerson, on_delete=models.CASCADE, related_name='+')
    contact_person = models.ForeignKey(KCPerson, on_delete=models.CASCADE, related_name='+')

    events = models.ManyToManyField(
        'KCEvent',
        through='KCEventPartner',
        through_fields=('evp_partner', 'evp_event'),
    )

class KCEvent(models.Model):

    name = models.CharField(max_length=250)
    start_date = models.DateField()
    end_date = models.DateField()

    participants = models.ManyToManyField(
        'Participant',
        through='KCEventRegistration',
        through_fields=('reg_event', 'reg_user'),
    )

    def _prepareMessageChurch(self, evp):
        # FIXME: create proper mail for invitation to churches.
        # - attaching the contract
        # - embedding information about login credentials
        # - embedding information about registration (with or without invitation?)
        subject = 'Event Kickoff - {0}'.format(
            self.name
        )
        message = 'Hello World!'
        sender = 'info@cvjm-rhein-lahn.de'
        recipients = [evp.evp_partner.contact_person.mail_addr, ]

        m = mail.EmailMessage(subject, message, sender, recipients)
        m.attach_file(evp.evp_doc_contract)
        return m

    def sendEventStartToChurches(self):
        # get all contact persons for the participating partners
        partners = self.kceventpartner_set.all()
        messages = []
        for kcevp in partners:
            messages.append(self._prepareMessageChurch(kcevp))

        if messages:
            with mail.get_connection() as connection:
                for m in messages:
                    m.connection = connection
                    m.send()

def getUploadPathEventPartner(instance, filename):
    # file will be uploaded to MEDIA_ROOT/kcevent/event_<id>/church_id/<filename>
    return 'kcevent/event_{0}/church_{1}/{2}'.format(
        instance.evp_event.id,
        instance.evp_partner.id,
        filename
    )

class KCEventPartner(models.Model):

    evp_event = models.ForeignKey(KCEvent, on_delete=models.CASCADE)
    evp_partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    # contract
    evp_doc_contract = models.FileField(upload_to=getUploadPathEventPartner, null=True)
    # statistics
    # Participants
    evp_apx_participant_m = models.PositiveSmallIntegerField()
    evp_apx_participant_w = models.PositiveSmallIntegerField()
    # Reloaded
    evp_apx_reloaded_m = models.PositiveSmallIntegerField()
    evp_apx_reloaded_w = models.PositiveSmallIntegerField()
    # Member
    evp_apx_member_m = models.PositiveSmallIntegerField()
    evp_apx_member_w = models.PositiveSmallIntegerField()


def getUploadPathEventRegistration(instance, filename):
    # file will be uploaded to MEDIA_ROOT/kcevent/event_<id>/user_<id>/<filename>
    return 'kcevent/event_{0}/user_{1}/{2}'.format(
        instance.reg_event.id,
        instance.reg_user.id, 
        filename
    )

class KCEventRegistration(models.Model):

    reg_time = models.DateTimeField()
    reg_event = models.ForeignKey(KCEvent, on_delete=models.CASCADE)
    reg_user = models.ForeignKey(Participant, on_delete=models.CASCADE)

    # further documentation
    reg_doc_pass = models.FileField(upload_to=getUploadPathEventRegistration)
    reg_doc_meddispense = models.FileField(upload_to=getUploadPathEventRegistration)
    reg_doc_consent = models.FileField(upload_to=getUploadPathEventRegistration)

