from django import forms
from kcevent.models import Participant, KCEventRegistration

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = [
            'first_name', 'last_name', 'street', 'house_number', 'zip_code', 'city',
            'phone', 'mail_addr', 'birthday', 'church', 'intolerances', 'nutrition', 
            'role', 'gender'
        ]

class KCEventRegistrationForm(forms.ModelForm):
    class Meta:
        model = KCEventRegistration
        fields = [
            'reg_doc_pass', 'reg_doc_meddispense', 'reg_doc_consent', 'reg_notes'
        ]