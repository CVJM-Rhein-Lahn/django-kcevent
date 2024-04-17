from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, resolve, path
from django.http import HttpResponse
from .models import KCEvent, KCPerson, Participant, Partner, KCEventPartner, KCEventRegistration, KCEventHost
from .models import KCTemplate, KCTemplateSet, KCEventDailyParticipant, KCEventParticipant
from .filters import custom_list_title_filter, is_27_and_older
from .actions import resendConfirmation, resendChurchNotification, bookDailyParticipant

class KCEventAdmin(admin.ModelAdmin):
    list_display = ["name", "host", "start_date", "end_date", "event_url", "registration_start", "registration_end", "template", "link_participants"]
    prepopulated_fields = {"event_url": ("name",)}

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<path:object_id>/participants', self.admin_site.admin_view(self.part_view), name='kcevent_kcevent_participants')
        ]
        print(my_urls + urls)
        return my_urls + urls

    def part_view(self, request, object_id=None):
        # here we can now built fancy (dynamic) forms according to the event object.
        evt = KCEvent.objects.get(id=object_id)
        days = evt.eventDays()
        print(evt, days)
        return HttpResponse('test')

    @admin.display(description=_("Participants list"))
    def link_participants(self, obj):
        url = "/admin/kcevent/kcevent/{:d}/participants".format(obj.id)
        #url_2 = reverse('kcevent_kcevent_participants', kwargs={'object_id': obj.id})
        #print(url)
        return format_html(
            "<a href=\"{}\">{}</a>",
            url,
            _("Go to list")
        )

class KCEventHostAdmin(admin.ModelAdmin):
    list_display = ["name", "representative", "contact_person"]

class KCEventNights(admin.TabularInline):
    model = KCEventDailyParticipant

class KCEventRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        "reg_event", "reg_user", "reg_status", "participant_age", "is_27", "nights", "reg_time",
        "confirmation_send", "confirmation_partner_send"
    ]
    list_filter = [
        "reg_status", "confirmation_send", "confirmation_partner_send", 
        ("reg_event__name", custom_list_title_filter(_("Events"))), is_27_and_older
    ]
    search_fields = ["reg_event__name", "reg_user__first_name", "reg_user__last_name"]
    ordering = ["reg_event", "reg_user"]
    actions = [resendConfirmation, resendChurchNotification, bookDailyParticipant]
    date_hierarchy = "reg_event__start_date"
    #list_editable = ["reg_status"]
    inlines = [
        KCEventNights
    ]

class KCEventPartnerAdmin(admin.ModelAdmin):
    list_display = ["evp_event", "evp_partner", "evp_doc_contract"]

class KCTemplateSetAdmin(admin.ModelAdmin):
    list_display = ["name",]
    
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

class KCEventDailyParticipantAdmin(admin.ModelAdmin):
    list_display = ["event", "participant", "day", "participation_type"]
    #search_fields = ["name"]

admin.site.register(KCEventHost, KCEventHostAdmin)
admin.site.register(KCTemplateSet, KCTemplateSetAdmin)
admin.site.register(KCTemplate, KCTemplateAdmin)
admin.site.register(KCEvent, KCEventAdmin)
admin.site.register(KCPerson, KCPersonAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(KCEventPartner, KCEventPartnerAdmin)
admin.site.register(KCEventRegistration, KCEventRegistrationAdmin)
admin.site.register(KCEventDailyParticipant, KCEventDailyParticipantAdmin)