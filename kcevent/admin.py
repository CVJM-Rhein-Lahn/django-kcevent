from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .models import KCEvent, KCPerson, Participant, Partner, KCEventPartner, KCEventRegistration, KCEventHost
from .models import KCTemplate, KCTemplateSet
from .filters import custom_list_title_filter, is_27_and_older
from .actions import resendConfirmation, resendChurchNotification, copyEvent

class KCEventPartnerInlineAdmin(admin.TabularInline):
    model = KCEventPartner

class KCTemplateInlineAdmin(admin.TabularInline):
    model = KCTemplate

class KCEventAdmin(admin.ModelAdmin):
    list_display = ["name", "host", "start_date", "end_date", "event_link", "registration_start", "registration_end", "template", "export_link"]
    prepopulated_fields = {"event_url": ("name",)}
    actions = [copyEvent]
    inlines = [KCEventPartnerInlineAdmin]

    @admin.display(description = _('Export'))
    def export_link(self, obj):
        url = reverse('downloadEventDocuments', kwargs={'event_url': obj.event_url})
        linkName = _('Documents')
        return format_html('<a href="{url}">{linkName}</a>'.format(url=url, linkName=linkName))

    @admin.display(description = _('Registration URL'))
    def event_link(self, obj):
        url = reverse('registerEvent', kwargs={'event_url': obj.event_url})
        return format_html('<a href="{url}" target="_blank">{linkName}</a>'.format(url=url, linkName=obj.event_url))

class KCEventHostAdmin(admin.ModelAdmin):
    list_display = ["name", "representative", "contact_person"]

class KCEventRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        "reg_event", "reg_user", "reg_status", "participant_age", "is_27", 
        "reg_time", "confirmation_send", "confirmation_partner_send"
    ]
    list_filter = [
        "reg_status", "confirmation_send", "confirmation_partner_send", 
        ("reg_event__name", custom_list_title_filter(_("Events"))), is_27_and_older
    ]
    search_fields = ["reg_event__name", "reg_user__first_name", "reg_user__last_name"]
    ordering = ["reg_event", "reg_user"]
    actions = [resendConfirmation, resendChurchNotification]
    date_hierarchy = "reg_event__start_date"

class KCEventPartnerAdmin(admin.ModelAdmin):
    list_display = ["evp_event", "evp_partner", "evp_doc_contract"]

class KCTemplateSetAdmin(admin.ModelAdmin):
    list_display = ["name",]
    inlines = [KCTemplateInlineAdmin]
    
class KCTemplateAdmin(admin.ModelAdmin):
    list_display = ["tpl_set", "tpl_type", "tpl_subject"]
    list_filter = [("tpl_set__name", custom_list_title_filter(_("Template set")))]

class KCPersonAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "phone", "mail_addr"]
    search_fields = ["last_name", "first_name"]

class ParticipantAdmin(admin.ModelAdmin):
    list_display = [
        "last_name", "first_name", "phone", "mail_addr", "birthday", "age", "church", 
        "intolerances", "nutrition", "lactose_intolerance", "celiac_disease", 
        "role", "gender"
    ]
    search_fields = ["last_name", "first_name", "events__name"]
    list_filter = [
        "nutrition", "lactose_intolerance", "celiac_disease", "role", "gender", 
        ("events__name", custom_list_title_filter(_("Events"))), 
        ("church__name", custom_list_title_filter(_("Church")))
    ]
    list_display_links = ["last_name", "first_name"]

class PartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "mail_addr", "representative", "contact_person"]
    search_fields = ["name"]

admin.site.register(KCEventHost, KCEventHostAdmin)
admin.site.register(KCTemplateSet, KCTemplateSetAdmin)
admin.site.register(KCTemplate, KCTemplateAdmin)
admin.site.register(KCEvent, KCEventAdmin)
admin.site.register(KCPerson, KCPersonAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(KCEventPartner, KCEventPartnerAdmin)
admin.site.register(KCEventRegistration, KCEventRegistrationAdmin)