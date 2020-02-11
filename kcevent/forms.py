from django import forms
from kcevent.models import Participant, KCEventRegistration
from django.utils.translation import ugettext_lazy as _

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = [
            'first_name', 'last_name', 'street', 'house_number', 'zip_code', 'city',
            'phone', 'mail_addr', 'birthday', 'church', 'intolerances', 'nutrition', 
            'role', 'gender', 'lactose_intolerance', 'celiac_disease'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': _('First name')}),
            'last_name': forms.TextInput(attrs={'placeholder': _('Surname')}),
            'street': forms.TextInput(attrs={'placeholder': _('Street')}),
            'house_number': forms.TextInput(attrs={'placeholder': _('House no.')}),
            'zip_code': forms.TextInput(attrs={'placeholder': _('Postal code')}),
            'city': forms.TextInput(attrs={'placeholder': _('City')}),
            'phone': forms.TextInput(attrs={'placeholder': _('Phone')}),
            'mail_addr': forms.TextInput(attrs={'placeholder': _('Mail address')}),
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'intolerances': forms.Textarea(attrs={'placeholder': _('Allergies / intolerances')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['church'].empty_label = _('Please choose your church')
        # replace empty choice
        self.fields['role'].widget.choices = [('', _('Please choose your role'))] + self.fields['role'].widget.choices[1:]
        self.fields['gender'].widget.choices = [('', _('Please choose your gender'))] + self.fields['gender'].widget.choices[1:]

class KCEventRegistrationForm(forms.ModelForm):
    class Meta:
        model = KCEventRegistration
        fields = [
            'reg_doc_pass', 'reg_doc_meddispense', 'reg_doc_consent', 'reg_notes',
            'reg_consent'
        ]
        widgets = {
            'reg_notes': forms.Textarea(attrs={'placeholder': _('Other communications')}),
        }

