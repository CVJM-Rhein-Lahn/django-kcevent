from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .models import KCEvent, KCPerson, Participant, Partner, KCEventPartner, KCEventRegistration
from .models import KCTemplate, KCTemplateSet, KCEventExportSetting
from .models import KCEventLocation
from .filters import custom_list_title_filter, is_27_and_older, is_event_future
from .actions import resendConfirmation, resendChurchNotification, copyEvent, syncEvent

class KCEventPartnerInlineAdmin(admin.TabularInline):
    model = KCEventPartner
    
class KCEventLocationAdmin(admin.ModelAdmin):
    model = KCEventLocation

class KCTemplateInlineAdmin(admin.TabularInline):
    model = KCTemplate

class KCEventExportSettingInlineAdmin(admin.StackedInline):
    model = KCEventExportSetting

class KCEventAdmin(admin.ModelAdmin):
    list_display = ["name", "host", "location", "start_date", "end_date", "event_link", "registration_start", "registration_end", "template", "exe_actions"]
    prepopulated_fields = {"event_url": ("name",)}
    actions = [copyEvent, syncEvent]
    inlines = [KCEventPartnerInlineAdmin, KCEventExportSettingInlineAdmin]

    list_filter = [
        "start_date", "name", is_event_future
    ]

    @admin.display(description = _('Actions'))
    def exe_actions(self, obj):
        links = [
            {
                'url': reverse('downloadEventDocuments', kwargs={'event_url': obj.event_url}),
                'name': _('Download documents')
            },
            {
                'url': reverse('admin:kcevent_kceventregistration_changelist') + '?reg_event__id__exact=' + str(obj.id),
                'name': _('Participants')
            },
            {
                'url': reverse('admin:kcevent_kceventregistration_add') + '?reg_event=' + str(obj.id),
                'name': _('Add participant')
            }
        ]
        return format_html(
            '<ul class="flat-action-list">' + 
            ''.join(
                [
                    '<li><a href="{url}">{linkName}</a></li>'.format(url=i['url'], linkName=i['name']) for i in links
                ]
            ) + 
            '</ul>'   
        )

    @admin.display(description = _('Registration URL'))
    def event_link(self, obj):
        url = reverse('registerEvent', kwargs={'event_url': obj.event_url})
        return format_html('<a href="{url}" target="_blank">{linkName}</a>'.format(url=url, linkName=obj.event_url))

class KCEventRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        "reg_event", "reg_user", "reg_status", "participant_age", "is_27", 
        "reg_time", "confirmation_send", "confirmation_partner_send"
    ]
    list_filter = [
        "reg_status", "confirmation_send", "confirmation_partner_send", 
        "reg_event", is_27_and_older
    ]
    search_fields = ["reg_event__name", "reg_user__first_name", "reg_user__last_name"]
    ordering = ["reg_event", "reg_user"]
    actions = [resendConfirmation, resendChurchNotification]
    date_hierarchy = "reg_event__start_date"

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
        ("church__name", custom_list_title_filter(_("Partner")))
    ]
    list_display_links = ["last_name", "first_name"]

class PartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "mail_addr", "representative", "contact_person"]
    search_fields = ["name"]

admin.site.register(KCTemplateSet, KCTemplateSetAdmin)
admin.site.register(KCTemplate, KCTemplateAdmin)
admin.site.register(KCEvent, KCEventAdmin)
admin.site.register(KCPerson, KCPersonAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(KCEventRegistration, KCEventRegistrationAdmin)
admin.site.register(KCEventLocation, KCEventLocationAdmin)