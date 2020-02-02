from django.contrib import admin
from .models import KCEvent, KCPerson, Participant, Partner, KCEventPartner, KCEventRegistration, KCEventHost
from .models import KCTemplate, KCTemplateSet

class KCEventAdmin(admin.ModelAdmin):
    prepopulated_fields = {"event_url": ("name",)}

admin.site.register(KCEventHost)
admin.site.register(KCTemplateSet)
admin.site.register(KCTemplate)
admin.site.register(KCEvent, KCEventAdmin)
admin.site.register(KCPerson)
admin.site.register(Participant)
admin.site.register(Partner)
admin.site.register(KCEventPartner)
admin.site.register(KCEventRegistration)