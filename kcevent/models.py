import os
from django.contrib import admin
from django.core import mail
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.template import Context, Template
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date
from .exceptions import NoTemplatesException
from . import logger

class KCTemplateSet(models.Model):
    class Meta:
        verbose_name = _('Template set')
        verbose_name_plural = _('Template sets')

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250, verbose_name=_('Name'))

    def __str__(self):
        return self.name


class KCTemplate(models.Model):
    class Meta:
        verbose_name =_('Template')
        verbose_name_plural =_('Templates')
        unique_together = (('tpl_set', 'tpl_type'),)

    class TemplateTypes(models.TextChoices):
        REGISTRATION_CONFIRMATION = 'registrationConfirmation', _('Confirm registration to participant')
        REGISTRATION_NOTIFICATION = 'registrationNotification', _('Confirm registration to church and host')
        FORM_LOGIN = 'formLogin', _('Notes during login to event')
        FORM_INTRODUCTION = 'formIntroduction', _('Introduction to event')

    id = models.AutoField(primary_key=True)
    tpl_set = models.ForeignKey(KCTemplateSet, on_delete=models.CASCADE, verbose_name=_('Template set'))
    tpl_type = models.CharField(
        max_length=50,
        choices=TemplateTypes.choices,
        verbose_name=_('Template type')
    )
    tpl_subject = models.CharField(max_length=255, verbose_name=_('Subject template'))
    tpl_content = models.TextField(verbose_name=_('Body template'))

    def __str__(self):
        return 'Template for set {0} / {1}: {2}'.format(
            self.tpl_set.name, 
            self.tpl_type, 
            self.tpl_subject
        )

class KCPerson(models.Model):
    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')

    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=120, verbose_name=_('First name'))
    last_name = models.CharField(max_length=120, verbose_name=_('Surname'))
    street = models.CharField(max_length=120, verbose_name=_('Street'))
    house_number = models.CharField(max_length=10, verbose_name=_('House no.'))
    city = models.CharField(max_length=120, verbose_name=_('City'))
    zip_code = models.CharField(max_length=10, verbose_name=_('Postal code'))
    phone = models.CharField(max_length=50, blank=True, verbose_name=_('Phone'))
    mail_addr = models.EmailField(verbose_name=_('Mail address'))
    createdTime = models.DateTimeField(auto_now_add=True, verbose_name=_('Created on'))
    updatedTime = models.DateTimeField(auto_now=True, verbose_name=_('Updated on'))

    def __str__(self):
        return '{0} {1}'.format(self.first_name, self.last_name)

    @property
    def fullname(self):
        return '{0} {1}'.format(self.first_name, self.last_name)

class Participant(KCPerson):
    class Meta:
        verbose_name = _('Participant')
        verbose_name_plural = _('Participants')

    class NutritionTypes(models.TextChoices):
        __empty__ = _('Please choose your nutrition')
        NUTRITION_REGULAR = 'RGL', _('Regular')
        NUTRITION_VEGETARIAN = 'VGT', _('Vegetarian')
        NUTRITION_VEGAN = 'VGN', _('Vegan')

    class ParticipantRoles(models.TextChoices):
        __empty__ = _('Please choose your role')
        ROLE_CONFIRMEE = 'CF', _('Confirmand')
        ROLE_RELOADED = 'RL', _('Reloaded')
        ROLE_STAFF = 'ST', _('Staff')

    class GenderTypes(models.TextChoices):
        __empty__ = _('Please choose your gender')
        GENDER_MALE = 'M', _('Male')
        GENDER_FEMALE = 'W', _('Female')
        GENDER_DIVERT = 'D', _('Divert')

    birthday = models.DateField(verbose_name=_('Birthday'))
    church = models.ForeignKey('Partner', null=True, on_delete=models.SET_NULL, verbose_name=_('Church'))
    intolerances = models.TextField(blank=True, default='', verbose_name=_('Intolerances'))
    nutrition = models.CharField(
        max_length=3,
        choices=NutritionTypes.choices,
        blank=True,
        default='',
        verbose_name=_('Nutrition')
    )
    lactose_intolerance = models.BooleanField(default=False, verbose_name=_('Lactose intolerance'))
    celiac_disease = models.BooleanField(default=False, verbose_name=_('Celiac disease'))
    role = models.CharField(
        max_length=2,
        choices=ParticipantRoles.choices,
        verbose_name=_('Role')
    )
    gender = models.CharField(
        max_length=1,
        choices=GenderTypes.choices,
        verbose_name=_('Gender')
    )

    events = models.ManyToManyField(
        'KCEvent',
        through='KCEventRegistration',
        through_fields=('reg_user', 'reg_event'),
        verbose_name=_('Events')
    )

    @property
    def nutrition_tolerances(self):
        n = str(self.get_nutrition_display())
        if self.lactose_intolerance:
            n += ', ' + str(_('Lactose intolerance'))
        if self.celiac_disease:
            n += ', ' + str(_('Celiac disease'))

        return n

    @admin.display(description=_("Age"))
    def age(self):
        age = 0
        if self.birthday:
            today = date.today()
            age = today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))

        return age

class Partner(models.Model):
    class Meta:
        verbose_name = _('Partner')
        verbose_name_plural = _('Partner')

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250, verbose_name=_('Name'))
    street = models.CharField(max_length=120, verbose_name=_('Street'))
    house_number = models.CharField(max_length=10, verbose_name=_('House no.'))
    city = models.CharField(max_length=120, verbose_name=_('City'))
    zip_code = models.CharField(max_length=10, verbose_name=_('Postal code'))
    mail_addr = models.EmailField(verbose_name=_('Mail address'))

    representative = models.ForeignKey(KCPerson, on_delete=models.CASCADE, related_name='+', verbose_name=_('Responsible person'))
    contact_person = models.ForeignKey(KCPerson, on_delete=models.CASCADE, related_name='+', verbose_name=_('Contact person'))

    events = models.ManyToManyField(
        'KCEvent',
        through='KCEventPartner',
        through_fields=('evp_partner', 'evp_event'),
        verbose_name=_('Events')
    )

    def __str__(self):
        return self.name

class KCEventHost(models.Model):
    class Meta:
        verbose_name = _('Event host')
        verbose_name_plural = _('Event hosts')

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250, verbose_name=_('Name'))
    street = models.CharField(max_length=120, verbose_name=_('Street'))
    house_number = models.CharField(max_length=10, verbose_name=_('House no.'))
    city = models.CharField(max_length=120, verbose_name=_('City'))
    zip_code = models.CharField(max_length=10, verbose_name=_('Postal code'))
    mail_addr = models.EmailField(verbose_name=_('Mail address'))
    website = models.URLField(blank=True, verbose_name=_('Website'))

    representative = models.ForeignKey(KCPerson, on_delete=models.CASCADE, related_name='+', verbose_name=_('Responsible person'))
    contact_person = models.ForeignKey(KCPerson, on_delete=models.CASCADE, related_name='+', verbose_name=_('Contact person'))

    def __str__(self):
        return self.name

class KCEvent(models.Model):
    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    id = models.AutoField(primary_key=True)
    host = models.ForeignKey(KCEventHost, on_delete=models.CASCADE, related_name='+', verbose_name=_('Host'), null=True)
    name = models.CharField(max_length=250, verbose_name=_('Name'))
    start_date = models.DateField(verbose_name=_('Start date'))
    end_date = models.DateField(verbose_name=_('End date'))
    registration_start = models.DateField(null=True, verbose_name=_('Registration start'))
    registration_end = models.DateField(null=True, verbose_name=_('Registration end'))
    event_url = models.SlugField(verbose_name=_('Registration URL'), help_text=_('SEO optimized location for register to event.'))
    reg_pwd = models.CharField(
        max_length=250, blank=True, verbose_name=_('Registration password'), 
        help_text=_('Password (can be empty) which is necessary in order to be able to register to event.')
    )
    template = models.ForeignKey(
        KCTemplateSet, on_delete=models.SET_NULL, null=True, verbose_name=_('Template set'),
        help_text=_('A set of templates used in order to send mails.')
    )

    participants = models.ManyToManyField(
        'Participant',
        through='KCEventRegistration',
        through_fields=('reg_event', 'reg_user'),
        verbose_name=_('Participants')
    )

    onSiteAttendance = models.BooleanField(default=True, verbose_name=_('On-site attendance'), \
        help_text=_('In case event is an on-site attendance event, further documents are requested by the participant during registration.'))
    requireDocuments = models.BooleanField(default=True, verbose_name=_('Require documents'), \
        help_text=_('Ask and require certain forms and documents from user to upload.'))

    def clean(self):
        validationErrors = {}

        # Validate event dates itself
        if self.start_date > self.end_date:
            validationErrors['start_date'] = ValidationError(_("Event start date cannot be after end date."))
            validationErrors['end_date'] = ValidationError(_("Event end date cannot be before start date."))

        # Validate registration date range.
        if self.registration_start is not None and self.registration_end is None:
            validationErrors['registration_end'] = ValidationError(_("Registration date range consists of start and end date!"))
        elif self.registration_start is None and self.registration_end is not None:
            validationErrors['registration_start'] = ValidationError(_("Registration date range consists of start and end date!"))
        elif self.registration_start is not None:
            if self.registration_start > self.start_date:
                validationErrors['registration_start'] = ValidationError(_("Usually an event registration should happen prior to the event itself!"))
            if self.registration_end > self.end_date:
                validationErrors['registration_end'] = ValidationError(_("A registration to the event should usually end latest on event start."))

        # Validate, that event URL is unique cross registration date range.
        evt = KCEvent.objects.filter(event_url=self.event_url)
        if self.id:
            evt = evt.exclude(id=self.id)
        if len(evt) > 0:
            validationErrors['event_url'] = ValidationError(_("Event URL must be unique."))

        if len(validationErrors) > 0:
            raise ValidationError(validationErrors)
    
    def formLogin(self):
        tpl = KCTemplate.objects.filter(
            tpl_set=self.template, tpl_type=KCTemplate.TemplateTypes.FORM_LOGIN
        ).first()
        dta = {
            'subject': None,
            'content': None
        }
        if tpl:
            context = Context({
                'event': self,
            })
            dta['subject'] = Template(tpl.tpl_subject).render(context)
            dta['content'] = Template(tpl.tpl_content).render(context)

        return dta

    def formIntroduction(self):
        tpl = KCTemplate.objects.filter(
            tpl_set=self.template, tpl_type=KCTemplate.TemplateTypes.FORM_INTRODUCTION
        ).first()
        dta = {
            'subject': None,
            'content': None
        }
        if tpl:
            context = Context({
                'event': self,
            })
            dta['subject'] = Template(tpl.tpl_subject).render(context)
            dta['content'] = Template(tpl.tpl_content).render(context)

        return dta

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

class KCEventRegistrationStateTypes(models.TextChoices):
    __empty__ = _('Please choose status of registration')
    REGTYPE_REGISTERED = 'registered', _('Registered')
    REGTYPE_ACTIVE = 'active', _('Active')
    REGTYPE_CANCELLED = 'cancelled', _('Cancelled')
    REGTYPE_DECLINED = 'declined', _('Declined')

class KCEventPartner(models.Model):
    class Meta:
        verbose_name = _('Event partner')
        verbose_name_plural = _('Event partners')

    id = models.AutoField(primary_key=True)
    evp_event = models.ForeignKey(KCEvent, on_delete=models.CASCADE, verbose_name=_('Event'))
    evp_partner = models.ForeignKey(Partner, on_delete=models.CASCADE, verbose_name=_('Event partner'))
    # contract
    evp_doc_contract = models.FileField(upload_to=getUploadPathEventPartner, null=True, blank=True, verbose_name=_('Contract'))
    # statistics
    # Participants
    evp_apx_participant_m = models.PositiveSmallIntegerField(default=0, verbose_name=_('Approx. no. of male par.'))
    evp_apx_participant_w = models.PositiveSmallIntegerField(default=0, verbose_name=_('Approx. no. of female par.'))
    # Reloaded
    evp_apx_reloaded_m = models.PositiveSmallIntegerField(default=0, verbose_name=_('Approx. no. of male reloaded'))
    evp_apx_reloaded_w = models.PositiveSmallIntegerField(default=0, verbose_name=_('Approx. no. of female reloaded'))
    # Member
    evp_apx_member_m = models.PositiveSmallIntegerField(default=0, verbose_name=_('Approx. no. of male members'))
    evp_apx_member_w = models.PositiveSmallIntegerField(default=0, verbose_name=_('Approx. no. of female members'))

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
        permissions = (
            ('can_download_regdocs', _('Can download registration documents')),
        )

    id = models.AutoField(primary_key=True)
    reg_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Registration time'))
    reg_event = models.ForeignKey(KCEvent, on_delete=models.CASCADE, verbose_name=_('Event'))
    reg_user = models.ForeignKey(Participant, on_delete=models.CASCADE, verbose_name=_('Person'))
    reg_notes = models.TextField(blank=True, verbose_name=_('Notes'))
    reg_consent = models.BooleanField(default=False, verbose_name=_('Consent parents'))

    reg_status = models.CharField(
        max_length=20,
        choices=KCEventRegistrationStateTypes.choices,
        default=KCEventRegistrationStateTypes.REGTYPE_REGISTERED,
        verbose_name=_('Registration status')
    )

    # further documentation
    reg_doc_pass = models.FileField(upload_to=getUploadPathEventRegistration, blank=True, verbose_name=_('Event passport'))
    reg_doc_meddispense = models.FileField(upload_to=getUploadPathEventRegistration, blank=True, verbose_name=_('Medical dispense'))
    reg_doc_consent = models.FileField(upload_to=getUploadPathEventRegistration, blank=True, verbose_name=_('Consent form'))

    # meta information for notification
    confirmation_send = models.BooleanField(default=False, verbose_name=_('Confirmation send'))
    confirmation_dt = models.DateTimeField(null=True, blank=True, verbose_name=_('Confirmation date/time'))
    confirmation_partner_send = models.BooleanField(default=False, verbose_name=_('Partner confirmation send'))
    confirmation_partner_dt = models.DateTimeField(null=True, blank=True, verbose_name=_('Partner confirmation date/time'))

    def __str__(self):
        # event ?
        event = self.reg_event.name if self.reg_event else '??'
        participant = str(self.reg_user) if self.reg_user else '??'
        return 'Registration "' + event + '": ' + participant

    @admin.display(description=_("Age"), ordering="-reg_user__birthday")
    def participant_age(self):
        age = 0
        if self.reg_user.birthday:
            today = self.reg_event.start_date
            age = today.year - self.reg_user.birthday.year - ((today.month, today.day) < (self.reg_user.birthday.month, self.reg_user.birthday.day))

        return age

    @admin.display(description=_("O27/U27"), boolean=True, ordering="reg_user__birthday")
    def is_27(self):
        age = 0
        if self.reg_user.birthday:
            today = self.reg_event.start_date
            age = today.year - self.reg_user.birthday.year - ((today.month, today.day) < (self.reg_user.birthday.month, self.reg_user.birthday.day))

        return age >= 27

    def clean(self):
        super().clean()
        errorDict = {}
        if self.confirmation_send and not self.confirmation_dt:
            errorDict['confirmation_dt'] = _('Confirmation date/time required if confirmation was sent.')
        if self.confirmation_partner_send and not self.confirmation_partner_dt:
            errorDict['confirmation_partner_dt'] = _('Confirmation date/time required if confirmation was sent.')

        if errorDict:
            raise ValidationError(errorDict)

    def updateFilePaths(self):
        changed = False
        user_name = self.reg_user.last_name.lower().replace(' ', '') + '_' + \
            self.reg_user.first_name.lower().replace(' ', '')
        if self.reg_doc_pass.name:
            oldPath = self.reg_doc_pass.path
            oldName, oldExt = os.path.splitext(os.path.basename(self.reg_doc_pass.name))
            newName = 'doc_pass_' + user_name + oldExt
            self.reg_doc_pass.name = getUploadPathEventRegistration(self, newName)
            newPath = os.path.join(settings.MEDIA_ROOT, self.reg_doc_pass.name)
            if oldPath != newPath:
                os.rename(oldPath, newPath)
                changed = True

        if self.reg_doc_meddispense.name:
            oldPath = self.reg_doc_meddispense.path
            oldName, oldExt = os.path.splitext(os.path.basename(self.reg_doc_meddispense.name))
            newName = 'doc_meddispense_' + user_name + oldExt
            self.reg_doc_meddispense.name = getUploadPathEventRegistration(self, newName)
            newPath = os.path.join(settings.MEDIA_ROOT, self.reg_doc_meddispense.name)
            if oldPath != newPath:
                os.rename(oldPath, newPath)
                changed = True

        if self.reg_doc_consent.name:
            oldPath = self.reg_doc_consent.path
            oldName, oldExt = os.path.splitext(os.path.basename(self.reg_doc_consent.name))
            newName = 'doc_consent_' + user_name + oldExt
            self.reg_doc_consent.name = getUploadPathEventRegistration(self, newName)
            newPath = os.path.join(settings.MEDIA_ROOT, self.reg_doc_consent.name)
            if oldPath != newPath:
                os.rename(oldPath, newPath)
                changed = True

        if changed:
            self.save()

    def sendConfirmation(self, request):
        # Find the right template.
        if not self.reg_event.template:
            raise NoTemplatesException('No template set defined for event {0}!'.format(self.reg_event.name))

        # find the right template
        tpl = KCTemplate.objects.filter(
            tpl_set=self.reg_event.template, tpl_type=KCTemplate.TemplateTypes.REGISTRATION_CONFIRMATION
        ).first()
        if not tpl:
            raise NoTemplatesException('No template defined for {0}'.format(KCTemplate.TemplateTypes.REGISTRATION_NOTIFICATION))

        sender = settings.NOTIFY_SENDER
        context = Context({
            'host': self.reg_event.host,
            'event': self.reg_event,
            'user': self.reg_user,
            'notes': self.reg_notes,
            'partner_name': self.reg_user.church.name
        })
        subject = Template(tpl.tpl_subject).render(context)
        message = Template(tpl.tpl_content).render(context)
        m = mail.EmailMessage(subject, message, sender, [self.reg_user.mail_addr,])
        sendResult = False
        try:
            sendResult = m.send()
        except ConnectionRefusedError as e:
            logger.error(f"Could not connect to smtp server: {e}")
            sendResult = False

        if sendResult:
            self.confirmation_send = True
            self.confirmation_dt = timezone.now()
            self.save()
            return True
        else:
            return False

    def notifyHostChurch(self, request):
        # Find the right template.
        if not self.reg_event.template:
            raise NoTemplatesException('No template set defined for event {0}!'.format(self.reg_event.name))

        # find the right template
        tpl = KCTemplate.objects.filter(
            tpl_set=self.reg_event.template, tpl_type=KCTemplate.TemplateTypes.REGISTRATION_NOTIFICATION
        ).first()
        if not tpl:
            raise NoTemplatesException('No template defined for {0}'.format(KCTemplate.TemplateTypes.REGISTRATION_NOTIFICATION))

        sender = settings.NOTIFY_SENDER
        messages = []
        for f in [self.reg_event.host, self.reg_user.church]:
            context = Context({
                'host': self.reg_event.host,
                'recipient': f,
                'event': self.reg_event,
                'user': self.reg_user,
                'notes': self.reg_notes,
                'partner_name': self.reg_user.church.name
            })
            subject = Template(tpl.tpl_subject).render(context)
            message = Template(tpl.tpl_content).render(context)
            m = mail.EmailMessage(subject, message, sender, [f.mail_addr,])
            if self.reg_doc_pass:
                m.attach_file(self.reg_doc_pass.path)
            if self.reg_doc_consent:
                m.attach_file(self.reg_doc_consent.path)
            if self.reg_doc_meddispense:
                m.attach_file(self.reg_doc_meddispense.path)
            messages.append(m)

        sendResult = False
        try:
            with mail.get_connection() as connection:
                    for m in messages:
                        m.connection = connection
                        if m.send():
                            sendResult = True
        except ConnectionRefusedError as e:
            # log somewhere.
            logger.error(f"Could not connect to smtp server: {e}")

        if sendResult:
            self.confirmation_partner_send = True
            self.confirmation_partner_dt = timezone.now()
            self.save()
            return True
        else:
            return False
