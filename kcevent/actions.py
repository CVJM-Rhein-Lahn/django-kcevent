from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse
### to be validated
from django.contrib.admin import helpers
from django.contrib.admin.decorators import action
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied, ValidationError
from django import forms
import datetime
### to be validated end

from .exceptions import NoTemplatesException
from .models import ParticipationTypes, KCEventDailyParticipant

@admin.action(
    permissions=["add"],
    description=_("Re-send participant confirmation")
)
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

@admin.action(
    permissions=["add"],
    description=_("Re-send registration confirmation to partner/church and organiser")
)
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


@admin.action(
    permissions=["add"],
    description=_("Book daily participant for %(verbose_name_plural)s"),
)
def bookDailyParticipant(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    app_label = opts.app_label

    class BookDateForm(forms.Form):
        day = forms.DateField(initial=datetime.date.today)
        participation_type = forms.ChoiceField(
            choices=ParticipationTypes.choices
        )
    form = BookDateForm()

    # Populate registrations, a data structure of all related objects that
    # will also be deleted.
    (
        deletable_objects,
        model_count,
        perms_needed,
        protected,
    ) = modeladmin.get_deleted_objects(queryset, request)
    registrations = queryset

    # The user has already confirmed the deletion.
    # Do the deletion and return None to display the change list view again.
    if request.POST.get("book_daily_participant") and not protected:
        if perms_needed:
            raise PermissionDenied

        form = BookDateForm(request.POST)
        if form.is_valid():
            n = len(queryset)
            errors = 0
            if n:
                for obj in queryset:
                    obj_display = str(obj)
                    day = form.cleaned_data['day']
                    participation_type = form.cleaned_data['participation_type']
                    evt = None
                    try:
                        evt = KCEventDailyParticipant.objects.get(registration=obj.id, day=day)
                    except:
                        evt = KCEventDailyParticipant.objects.create(registration=obj, day=day, participation_type=participation_type)
                    evt.participation_type = participation_type
                    try:
                        validMessages = evt.clean()
                        evt.save()
                    except ValidationError as e:
                        n -= 1
                        errors += 1
                
                if n > 0:
                    modeladmin.message_user(
                        request,
                        _("Successfully booked %(count)d %(items)s.")
                        % {"count": n, "items": model_ngettext(modeladmin.opts, n)},
                        messages.SUCCESS,
                    )
                if errors > 0:
                    modeladmin.message_user(
                        request,
                        _("Failed booking %(count)d %(items)s.")
                        % {"count": errors, "items": model_ngettext(modeladmin.opts, errors)},
                        messages.ERROR,
                    )

            # Return None to display the change list page again.
            return None

    objects_name = model_ngettext(queryset)

    if perms_needed or protected:
        title = _("Cannot delete %(name)s") % {"name": objects_name}
    else:
        title = _("Book daily participant")

    context = {
        **modeladmin.admin_site.each_context(request),
        "title": title,
        "subtitle": None,
        "objects_name": str(objects_name),
        "registrations": [registrations],
        "model_count": dict(model_count).items(),
        "queryset": queryset,
        "perms_lacking": perms_needed,
        "protected": protected,
        "opts": opts,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
        "media": modeladmin.media,
        "form": form,
    }

    request.current_app = modeladmin.admin_site.name

    # Display the confirmation page
    return TemplateResponse(
        request,
        "admin/book_daily_participant.html",
        context,
    )

