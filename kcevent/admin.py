from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import KCEvent, KCPerson, Participant, Partner, KCEventPartner, KCEventRegistration, KCEventHost
from .models import KCTemplate, KCTemplateSet
from .exceptions import NoTemplatesException

class KCEventAdmin(admin.ModelAdmin):
    list_display = ["name", "host", "start_date", "end_date", "event_url", "registration_start", "registration_end", "template"]
    prepopulated_fields = {"event_url": ("name",)}

class KCEventHostAdmin(admin.ModelAdmin):
    list_display = ["name", "representative", "contact_person"]

@admin.action(description=_("Re-send participant confirmation"))
def resendConfirmation(modeladmin, request, queryset):
    for f in queryset:
        try:
            if not f.sendConfirmation():
                modeladmin.message_user(request, _("Sending confirmation message to %(regUser)s on %(regEvent)s failed" % {
                    "regUser": str(f.reg_user), 
                    "regEvent": str(f.reg_event)
                }))
        except NoTemplatesException as e:
            modeladmin.message_user(request, _("No template defined when sending confirmation message to %(regUser)s on %(regEvent)s" % {
                "regUser": str(f.reg_user), 
                "regEvent": str(f.reg_event)
            }))

class KCEventRegistrationAdmin(admin.ModelAdmin):
    list_display = ["reg_event", "reg_user", "reg_time", "confirmation_send", "confirmation_dt"]
    ordering = ["reg_event", "reg_user"]
    actions = [resendConfirmation]

class KCEventPartnerAdmin(admin.ModelAdmin):
    list_display = ["evp_event", "evp_partner", "evp_doc_contract"]

class KCTemplateSetAdmin(admin.ModelAdmin):
    list_display = ["name",]
    
class KCTemplateAdmin(admin.ModelAdmin):
    list_display = ["tpl_set", "tpl_type", "tpl_subject"]

admin.site.register(KCEventHost, KCEventHostAdmin)
admin.site.register(KCTemplateSet, KCTemplateSetAdmin)
admin.site.register(KCTemplate, KCTemplateAdmin)
admin.site.register(KCEvent, KCEventAdmin)
admin.site.register(KCPerson)
admin.site.register(Participant)
admin.site.register(Partner)
admin.site.register(KCEventPartner, KCEventPartnerAdmin)
admin.site.register(KCEventRegistration, KCEventRegistrationAdmin)