from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from .exceptions import NoTemplatesException

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
def resendChurchNotification(modeladmin, request, queryset):
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