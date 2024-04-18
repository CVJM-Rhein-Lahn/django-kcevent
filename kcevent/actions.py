from typing import List
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from .exceptions import NoTemplatesException
from .models import KCEventRegistration, KCEvent
from .exports import GoogleSheetExporter

@admin.action(description=_("Re-send participant confirmation"))
def resendConfirmation(modeladmin, request, queryset):
    for f in queryset:
        try:
            if not f.sendConfirmation(request):
                modeladmin.message_user(request, _("Sending confirmation message to %(regUser)s on %(regEvent)s failed" % {
                    "regUser": str(f.reg_user), 
                    "regEvent": str(f.reg_event)
                }), level=messages.ERROR)
        except NoTemplatesException as e:
            modeladmin.message_user(request, _("No template defined when sending confirmation message to %(regUser)s on %(regEvent)s" % {
                "regUser": str(f.reg_user), 
                "regEvent": str(f.reg_event)
            }), level=messages.ERROR)

@admin.action(description=_("Re-send registration confirmation to partner/church and organiser"))
def resendChurchNotification(modeladmin, request, queryset: List[KCEventRegistration]):
    for f in queryset:
        try:
            if not f.notifyHostChurch(request):
                modeladmin.message_user(request, _("Sending confirmation message to %(regUser)s on %(regEvent)s failed" % {
                    "regUser": str(f.reg_user), 
                    "regEvent": str(f.reg_event)
                }), level=messages.ERROR)
        except NoTemplatesException as e:
            modeladmin.message_user(request, _("No template defined when sending confirmation message to %(regUser)s on %(regEvent)s" % {
                "regUser": str(f.reg_user), 
                "regEvent": str(f.reg_event)
            }), level=messages.ERROR)

@admin.action(description=_("Copy event in new one"))
def copyEvent(modeladmin, request, queryset: List[KCEvent]):
    if len(queryset) > 1:
        modeladmin.message_user(request, _("%(eventCount)d events were selected. Only one event must be selected!" % {
                "eventCount": len(queryset)
            }), level=messages.ERROR)
    else:
        for f in queryset:
            newName = f.name + ' (' + _('Copy') + ')'
            newEvent = KCEvent.objects.create(
                host = f.host,
                name = newName,
                start_date = f.start_date,
                end_date = f.end_date,
                registration_start = f.registration_start,
                registration_end = f.registration_end,
                reg_pwd = f.reg_pwd,
                template = f.template,
                event_url = slugify(newName),
                onSiteAttendance = f.onSiteAttendance,
                requireDocuments = f.requireDocuments
            )
            newEvent.save()

@admin.action(description=_("Sync event"))
def syncEvent(modeladmin, request, queryset: List[KCEvent]):
    if len(queryset) > 0:
        exporter = GoogleSheetExporter()
        for event in queryset:
            exporter.exportEvent(event)
