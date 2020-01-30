from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core import mail

class KCPerson(models.Model):
    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')

    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    street = models.CharField(max_length=120)
    house_number = models.CharField(max_length=10)
    city = models.CharField(max_length=120)
    zip_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=50, blank=True)
    mail_addr = models.EmailField()

    def __str__(self):
        return '{0} {1}'.format(self.first_name, self.last_name)

class Participant(KCPerson):
    class Meta:
        verbose_name = _('Participant')
        verbose_name_plural = _('Participants')

    class NutritionTypes(models.TextChoices):
        NUTRITION_REGULAR = 'RGL', _('Regular')
        NUTRITION_VEGETARIAN = 'VGT', _('Vegetarian')
        NUTRITION_VEGAN = 'VGN', _('Vegan')

    class ParticipantRoles(models.TextChoices):
        ROLE_CONFIRMEE = 'CF', _('Confirmand')
        ROLE_RELOADED = 'RL', _('Reloaded')
        ROLE_STAFF = 'ST', _('Staff')

    class GenderTypes(models.TextChoices):
        GENDER_MALE = 'M', _('Male')
        GENDER_FEMALE = 'W', _('Female')
        GENDER_DIVERT = 'D', _('Divert')

    birthday = models.DateField()
    church = models.ForeignKey('Partner', null=True, on_delete=models.SET_NULL)
    intolerances = models.TextField(blank=True)
    nutrition = models.CharField(
        max_length=3,
        choices=NutritionTypes.choices,
    )
    lactose_intolerance = models.BooleanField(default=False)
    celiac_disease = models.BooleanField(default=False)
    role = models.CharField(
        max_length=2,
        choices=ParticipantRoles.choices,
    )
    gender = models.CharField(
        max_length=1,
        choices=GenderTypes.choices,
    )

class Partner(models.Model):
    class Meta:
        verbose_name = _('Partner')
        verbose_name_plural = _('Partner')

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

    def __str__(self):
        return self.name

class KCEvent(models.Model):
    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    name = models.CharField(max_length=250)
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start = models.DateField(null=True)
    registration_end = models.DateField(null=True)
    event_url = models.SlugField()
    reg_pwd = models.CharField(max_length=250, blank=True)

    participants = models.ManyToManyField(
        'Participant',
        through='KCEventRegistration',
        through_fields=('reg_event', 'reg_user'),
    )

    def __str__(self):
        return self.name

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
    class Meta:
        verbose_name = _('Event Partner')
        verbose_name_plural = _('Event Partners')

    evp_event = models.ForeignKey(KCEvent, on_delete=models.CASCADE)
    evp_partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    # contract
    evp_doc_contract = models.FileField(upload_to=getUploadPathEventPartner, null=True)
    # statistics
    # Participants
    evp_apx_participant_m = models.PositiveSmallIntegerField(default=0)
    evp_apx_participant_w = models.PositiveSmallIntegerField(default=0)
    # Reloaded
    evp_apx_reloaded_m = models.PositiveSmallIntegerField(default=0)
    evp_apx_reloaded_w = models.PositiveSmallIntegerField(default=0)
    # Member
    evp_apx_member_m = models.PositiveSmallIntegerField(default=0)
    evp_apx_member_w = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        # event ?
        event = self.evp_event.name if self.evp_event else '??'
        partner = self.evp_partner.name if self.evp_partner else '??'
        return 'Partnership "' + event + '" <> "' + partner + '"'

def getUploadPathEventRegistration(instance, filename):
    # file will be uploaded to MEDIA_ROOT/kcevent/event_<id>/user_<id>/<filename>
    return 'kcevent/event_{0}/user_{1}/{2}'.format(
        instance.reg_event.id,
        instance.reg_user.id, 
        filename
    )

class KCEventRegistration(models.Model):
    class Meta:
        verbose_name = _('Event registration')
        verbose_name_plural = _('Event registrations')

    reg_time = models.DateTimeField(auto_now_add=True)
    reg_event = models.ForeignKey(KCEvent, on_delete=models.CASCADE)
    reg_user = models.ForeignKey(Participant, on_delete=models.CASCADE)
    reg_notes = models.TextField(blank=True)

    # further documentation
    reg_doc_pass = models.FileField(upload_to=getUploadPathEventRegistration)
    reg_doc_meddispense = models.FileField(upload_to=getUploadPathEventRegistration, null=True, blank=True)
    reg_doc_consent = models.FileField(upload_to=getUploadPathEventRegistration)

    def __str__(self):
        # event ?
        event = self.reg_event.name if self.reg_event else '??'
        participant = str(self.reg_user) if self.reg_user else '??'
        return 'Registration "' + event + '": ' + participant

