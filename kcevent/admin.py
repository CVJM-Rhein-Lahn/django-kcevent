from django.contrib import admin
from .models import KCEvent, KCPerson, Participant, Partner, KCEventPartner, KCEventRegistration

admin.site.register(KCEvent)
admin.site.register(KCPerson)
admin.site.register(Participant)
admin.site.register(Partner)
admin.site.register(KCEventPartner)
admin.site.register(KCEventRegistration)