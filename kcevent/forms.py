from django import forms
from kcevent.models import Participant, KCEventRegistration
from kcevent.models import (
    KCEmergencyContact,
    ParticipantRole,
    KCEventRegistrationStateTypes,
    Partner,
    KCEvent
)
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = [
            "church",
            "role",
            "first_name",
            "last_name",
            "gender",
            "birthday",
            "street",
            "house_number",
            "zip_code",
            "city",
            "mail_addr",
            "phone",
            "nutrition",
            "lactose_intolerance",
            "celiac_disease",
            "intolerances",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": _("First name")}),
            "last_name": forms.TextInput(attrs={"placeholder": _("Surname")}),
            "street": forms.TextInput(attrs={"placeholder": _("Street")}),
            "house_number": forms.TextInput(attrs={"placeholder": _("House no.")}),
            "zip_code": forms.TextInput(attrs={"placeholder": _("Postal code")}),
            "city": forms.TextInput(attrs={"placeholder": _("City")}),
            # Phone pattern DIN norm: (\+[0-9]{1,3}\s|00[0-9]{1,3}\s|0[1-9]{1})[0-9]+\s[0-9]+(-[0-9]+)?
            "phone": forms.TelInput(
                attrs={
                    "placeholder": _("Phone"),
                    #"pattern": "(.*\\d+.*)",
                    "required": True,
                }
            ),
            "mail_addr": forms.EmailInput(attrs={"placeholder": _("Mail address")}),
            "birthday": forms.DateInput(attrs={"type": "date"}, format='%Y-%m-%d'),
            "intolerances": forms.Textarea(
                attrs={"placeholder": _("Allergies / intolerances"), "rows": 2}
            ),
        }

    def __init__(self, event: KCEvent, *args, **kwargs):
        print(vars(kwargs['instance']))
        super().__init__(*args, **kwargs)
        self._event = event

        self._session_fields = {"_part_unique_id": None}

        partners = event.partners.get_queryset()
        roles = ParticipantRole.objects.filter(event=self._event)
        self.is_confirm_overview: bool = False
        self.fields["church"].empty_label = _("Please choose your church/organisation")
        self.fields["church"].queryset = partners
        if partners.count() <= 1:
            self.fields["church"].widget = self.fields["church"].hidden_widget()
        if partners.count() == 1:
            self.initial["church"] = partners[0]

        self.fields["role"].empty_label = _("Please choose your role")
        self.fields["role"].queryset = roles
        if roles.count() <= 1:
            self.fields["role"].widget = self.fields["role"].hidden_widget()
        if roles.count() == 1:
            self.initial["role"] = roles[0]

        if self._event.onSiteAttendance:
            self.fields["nutrition"].widget.attrs["required"] = "required"
            self.fields["nutrition"].formgridcls = 'short'

    def is_valid(self, *args, confirmOverview: bool = False, **kwargs):
        self.is_confirm_overview = confirmOverview
        return super().is_valid()
    
    @property
    def partner(self) -> Partner | None:
        return self.cleaned_data.get('church')

    def clean_nutrition(self):
        # check if we're on-site attendance - in this case, this
        # document is mandatory!
        cleanedData = self.cleaned_data.get("nutrition")
        if self._event.onSiteAttendance and (cleanedData is None or cleanedData == ""):
            raise forms.ValidationError(_("Nutrition is mandatory."))

        return cleanedData
    
    def clean_phone(self):
        cleaned_data = self.cleaned_data.get("phone")
        if cleaned_data is None or cleaned_data == "":
            raise forms.ValidationError(_("Phone number is mandatory."))
        
        phone_number: str = cleaned_data.strip() \
            .replace('(', '') \
            .replace(')', '') \
            .replace(' ', '') \
            .replace('-', '')
        
        # remove international parts...
        phone_number_numeric: str = phone_number.replace('+', '')
        if not phone_number_numeric.isnumeric():
            raise forms.ValidationError(_("Phone number must be numeric with optional country code prefix +."))
        
        return phone_number

class KCEventRegistrationForm(forms.ModelForm):
    class Meta:
        model = KCEventRegistration
        fields = [
            "reg_event",
            "reg_user",
            "reg_doc_pass",
            "reg_doc_meddispense",
            "reg_doc_consent",
            "reg_adddata",
            "reg_notes",
            "reg_consent_terms",
            "reg_consent_privacy",
            "reg_consent",
        ]
        widgets = {
            "reg_event": forms.HiddenInput(),
            "reg_user": forms.HiddenInput(),
            "reg_notes": forms.Textarea(
                attrs={"placeholder": _("Other communications"), 'rows': 3}
            ),
        }

    def __init__(self, event: KCEvent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event = event
        self._session_fields = {"_reg_unique_id": None}
        self.is_confirm_overview: bool = False
        for k, v in self.fields.items():
            if k.startswith("reg_doc_"):
                self.fields[k].widget.attrs["accept"] = "image/*,.pdf,application/pdf"
                
        if not self._event.requireDocuments:
            self.fields["reg_doc_consent"].widget = self.fields["reg_doc_consent"].hidden_widget()
            self.fields["reg_doc_pass"].widget = self.fields["reg_doc_pass"].hidden_widget()
            self.fields["reg_doc_meddispense"].widget = self.fields["reg_doc_meddispense"].hidden_widget()
        
        if self.has_consent_terms:        
            self.fields["reg_consent_terms"].formgridcls = 'full'
            self.fields["reg_consent_terms"].widget.attrs["required"] = "required"
        else:
            self.fields["reg_consent_terms"].widget = self.fields["reg_consent_terms"].hidden_widget()
        self.fields["reg_consent_privacy"].formgridcls = 'full'
        self.fields["reg_consent_privacy"].widget.attrs["required"] = "required"
        self.fields["reg_consent"].formgridcls = 'full'
        self.fields["reg_consent"].widget.attrs["required"] = "required"
        if self.instance:
            self.fields['reg_adddata'].widget.instance = self.instance
            if not self._event.has_regform_schema:
                self.fields.pop("reg_adddata")

    def is_valid(self, *args, confirmOverview: bool = False, **kwargs):
        self.is_confirm_overview = confirmOverview
        return super().is_valid()

    def clean_reg_consent(self):
        cleanedData = self.cleaned_data.get("reg_consent")
        if not cleanedData:
            raise forms.ValidationError(_("You must consent to the registration!"))

        return cleanedData

    def clean_reg_consent_privacy(self):
        cleanedData = self.cleaned_data.get("reg_consent_privacy")
        if not cleanedData:
            raise forms.ValidationError(_("You must consent to the privacy policy!"))

        return cleanedData

    def clean_reg_consent_terms(self):
        cleanedData = self.cleaned_data.get("reg_consent_terms")
        if not cleanedData and self.is_confirm_overview and self.has_consent_terms:
            raise forms.ValidationError(
                _("You must consent to the partners general terms and conditions!")
            )

        return cleanedData

    def clean_reg_doc_pass(self):
        cleanedData = self.cleaned_data.get("reg_doc_pass")
        # check if we're on-site attendance - in this case, this
        # document is mandatory!
        if self._event.requireDocuments and not cleanedData:
            raise forms.ValidationError(_("Event passport is mandatory."))
        return cleanedData

    def clean_reg_doc_consent(self):
        cleanedData = self.cleaned_data.get("reg_doc_consent")
        # check if we're on-site attendance - in this case, this
        # document is mandatory!
        if self._event.requireDocuments and not cleanedData:
            raise forms.ValidationError(_("Consent document is mandatory."))

        return cleanedData

    @property
    def price(self):
        price = self.instance.price

        if price:
            return "{:.2f} {:s}".format(price.price, price.currency)
        else:
            return ""

    @property
    def has_consent_terms(self):
        return self.instance.partner and self.instance.partner.evp_doc_policy

    @property
    def consent_terms_url(self):
        if self.instance.partner and self.instance.partner.evp_doc_policy:
            return self.instance.partner.evp_doc_policy
        else:
            return None

    def clean(self):
        cleaned_data = super().clean()  # noqa: F841
        # we need user information
        firstName = self.data.get("first_name")
        lastName = self.data.get("last_name")
        birthday = self.data.get("birthday")
        mailAddr = self.data.get("mail_addr")
        # find event
        evt = self._event
        # now check if there is already an registration known.
        try:
            reg = KCEventRegistration.objects.get(
                Q(reg_user__first_name=firstName, reg_user__last_name=lastName, reg_user__birthday=birthday, reg_user__mail_addr=mailAddr),
                Q(reg_event=evt) & ~Q(reg_status=KCEventRegistrationStateTypes.REGTYPE_CANCELLED)
            )
        except KCEventRegistration.DoesNotExist:
            pass
        else:
            if reg.id != self.get_unique_id() or self.get_unique_id is None:
                if reg.reg_status == KCEventRegistrationStateTypes.REGTYPE_INCOMPLETE:
                    # if there is already an incomplete registration, drop the incomplete one.
                    reg.reg_status = KCEventRegistrationStateTypes.REGTYPE_CANCELLED
                    reg.save()
                else:
                    raise forms.ValidationError(
                        _("You're already registered to this event.")
                    )


class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = KCEmergencyContact
        fields = [
            "first_name",
            "last_name",
            "street",
            "house_number",
            "zip_code",
            "city",
            "phone",
            "mail_addr",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": _("First name")}),
            "last_name": forms.TextInput(attrs={"placeholder": _("Surname")}),
            "street": forms.TextInput(attrs={"placeholder": _("Street")}),
            "house_number": forms.TextInput(attrs={"placeholder": _("House no.")}),
            "zip_code": forms.TextInput(attrs={"placeholder": _("Postal code")}),
            "city": forms.TextInput(attrs={"placeholder": _("City")}),
            # Phone pattern DIN norm: (\+[0-9]{1,3}\s|00[0-9]{1,3}\s|0[1-9]{1})[0-9]+\s[0-9]+(-[0-9]+)?
            "phone": forms.TextInput(
                attrs={
                    "placeholder": _("Phone"),
                    "pattern": "(.*\\d+.*)",
                    "required": True,
                }
            ),
            "mail_addr": forms.EmailInput(attrs={"placeholder": _("Mail address")}),
        }

    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event = event
        self.is_confirm_overview: bool = False

    def is_valid(self, *args, confirmOverview: bool = False, **kwargs):
        self.is_confirm_overview = confirmOverview
        return super().is_valid()

class PreviewForm(forms.Form):
    
    class Meta:
        fields = [
        ]
        
    base_fields = {}
    
    def __init__(self, event, form_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.event = event
        self.form_list = form_list
        for form in self.form_list.keys():
            self.form_list[form].is_valid()
            for field in self.form_list[form].fields.values():
                field.disabled = True
                if field.label == 'Geburtstag':
                    print(vars(field))
                # remove all placeholders in widgets
                try:
                    if field.widget.attrs['placeholder']:
                        field.widget.attrs.pop('placeholder')
                except KeyError:
                    pass
    
    @property
    def has_price(self) -> bool:
        reg = self.reg_form
        if reg:
            return reg.price and self.event.enablePrices
        else:
            return False
    
    @property
    def reg_form(self) -> KCEventRegistrationForm | None:
        for f in self.form_list.values():
            if isinstance(f, KCEventRegistrationForm):
                return f
            
        return None
    
    @property
    def media(self):
        media = super().media
        for form in self.form_list.values():
            for field in form.fields.values():
                media += field.widget.media
        return media
        
    def __repr__(self):
        if self._errors is None:
            is_valid = "Unknown"
        else:
            is_valid = self.is_bound and not self._errors
        return "<%(cls)s bound=%(bound)s, valid=%(valid)s, fields=(%(fields)s), forms=(%(forms)s)>" % {
            "cls": self.__class__.__name__,
            "bound": self.is_bound,
            "valid": is_valid,
            "fields": ";".join(self.fields),
            "forms": ";".join(self.form_list)
        }

