TPL__REGISTRATION_CONFIRMATION__SUBJECT = 'Registrierungsbestätigung für {{ event.name }}'
TPL__REGISTRATION_CONFIRMATION__CONTENT = '''{% load i18n %}
Liebe/r {{ user.fullname }},

vielen Dank für Deine Anmeldung zu {{ event.name }}. Diese wird nun bearbeitet. 
In den nächsten Wochen erhältst du eine offizielle Anmeldebestätigung. Damit ist Deine Teilnahme verbindlich.

Die Veranstaltung findet vom {{ event.start_date }} bis {{ event.end_date }} statt. Die Packliste sowie der Freizeitpass werden zeitnah vor dem {{ event.name }} verschickt. 

Bei der Registrierung hast Du folgende Informationen hinterlassen:
Name: {{ user.fullname }}
Anschrift: {{ user.street }} {{ user.house_number }}, {{ user.zip_code }} {{ user.city }}
Telefon: {{ user.phone }}
E-Mail Adresse: {{ user.mail_addr }}

Geburtsdatum: {{ user.birthday }}
Geschlecht: {{ user.get_gender_display }}
Kirchengemeinde/Organisation: {{ partner_name }}
Rolle: {{ user.get_role_display }}

Ernährung: {{ user.nutrition_tolerances }}

Unverträglichkeiten: 
{{ user.intolerances }}

Anmerkungen: 
{{ notes }}

Bitte teile uns jede Änderung mit, sodass wir entsprechend richtig planen können.
Wenn Du irgendeine Frage hast, kannst Du jederzeit mit uns in Kontakt treten.

Viele Grüße,
{{ event.name }} Team

---

{{ event.host.name }}
{% trans "Website" %}: {{ event.host.website }}
{% trans "Contact" %}: {{ event.host.mail_addr }}
'''

TPL__REGISTRATION_NOTIFICATION__SUBJECT = 'Neue Registrierung für {{ event.name }}'
TPL__REGISTRATION_NOTIFICATION__CONTENT = '''{% load i18n %}
Hallo {{ recipient.name }},

es gab eine neue Registrierung für die Veranstaltung "{{ event.name }}".

Registriert hat sich:
Name: {{ user.fullname }}
Anschrift: {{ user.street }} {{ user.house_number }}, {{ user.zip_code }} {{ user.city }}
Telefon: {{ user.phone }}
E-Mail Adresse: {{ user.mail_addr }}

Geburtsdatum: {{ user.birthday }}
Geschlecht: {{ user.get_gender_display }}
Kirchengemeinde: {{ partner_name }}
Rolle: {{ user.get_role_display }}

Anmerkungen: 
{{ notes }}

Bitte beachten Sie den Datenschutz. 

Viele Grüße,
{{ event.name }} Team

---

{{ event.host.name }}
{% trans "Website" %}: {{ event.host.website }}
{% trans "Contact" %}: {{ event.host.mail_addr }}
'''

TPL__FORM_LOGIN__SUBJECT = 'Anmeldung: {{ event.name }}'
TPL__FORM_LOGIN__CONTENT = '''
<p>Bitte gib das Passwort aus den Anmeldeunterlagen ein. Diese wurden durch die jeweiligen Kirchengemeinde/Organiation ausgegeben.</p>
'''

TPL__FORM_INTRODUCTION__SUBJECT = 'Anmeldung {{ event.name }}'
TPL__FORM_INTRODUCTION__CONTENT = '''Wir freuen uns über Deine Teilnahme bei {{ event.name }}
<p>Nach erfolgter Anmeldung schicken wir Dir zunächst eine Eingangsbestätigung per E-Mail zu. 
Die verbindliche Buchungsbestätigung senden wir Dir in den kommenden Wochen ebenfalls per E-Mail zu.</p>
'''