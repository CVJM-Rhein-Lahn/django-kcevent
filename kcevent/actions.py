import logging
from typing import List
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone as dj_timezone
from .exceptions import NoTemplatesException
from .models import KCEventRegistration, KCEvent, KCEventRegistrationStateTypes, ZitadelRoleAssignment, ZitadelUserMapping
from .exports import GoogleSheetExporter
from . import zitadel_client

logger = logging.getLogger(__name__)

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


@admin.action(description=_("Confirm registrations and assign Zitadel roles"))
def confirmRegistrationsAndAssignRoles(
    modeladmin, request, queryset: List[KCEventRegistration]
):
    confirmed = 0
    errors = 0
    for reg in queryset:
        if reg.reg_status in (
            KCEventRegistrationStateTypes.REGTYPE_CANCELLED,
        ):
            continue

        reg.reg_status = KCEventRegistrationStateTypes.REGTYPE_CONFIRMED
        reg.save()
        confirmed += 1

        participant = reg.reg_user
        event_url = reg.reg_event.event_url
        role = participant.role
        role_slug = slugify(role.name) if role else "participant"
        role_name = f"event_{event_url}_{role_slug}"

        try:
            zitadel_mapping = participant.zitadel_mapping
        except Exception:
            zitadel_mapping = None

        if not zitadel_mapping or not zitadel_mapping.zitadel_user_id:
            modeladmin.message_user(
                request,
                _("No Zitadel account found for %(user)s – role not assigned.") % {
                    "user": str(participant)
                },
                level=messages.WARNING,
            )
            errors += 1
            continue

        role_ok = zitadel_client.get_or_create_role(role_name)
        if not role_ok:
            modeladmin.message_user(
                request,
                _("Could not create Zitadel role %(role)s for %(user)s.") % {
                    "role": role_name, "user": str(participant)
                },
                level=messages.WARNING,
            )
            errors += 1
            continue

        grant_id = zitadel_client.add_user_role(
            zitadel_mapping.zitadel_user_id, role_name
        )
        if grant_id:
            ZitadelRoleAssignment.objects.update_or_create(
                registration=reg,
                role_name=role_name,
                defaults={
                    "zitadel_grant_id": grant_id,
                    "assigned_at": dj_timezone.now(),
                },
            )
        else:
            modeladmin.message_user(
                request,
                _("Could not assign Zitadel role %(role)s to %(user)s.") % {
                    "role": role_name, "user": str(participant)
                },
                level=messages.WARNING,
            )
            errors += 1

    if confirmed:
        modeladmin.message_user(
            request,
            _("%(count)d registration(s) confirmed and Zitadel roles assigned.") % {
                "count": confirmed
            },
        )
    if errors:
        modeladmin.message_user(
            request,
            _("%(count)d error(s) occurred during Zitadel role assignment. See warnings above.") % {
                "count": errors
            },
            level=messages.ERROR,
        )


@admin.action(description=_("Provision Zitadel accounts for participants"))
def provisionZitadelAccounts(
    modeladmin, request, queryset: List[KCEventRegistration]
):
    created = 0
    skipped = 0
    errors = 0

    for reg in queryset:
        participant = reg.reg_user

        try:
            existing = participant.zitadel_mapping
            if existing.zitadel_user_id:
                skipped += 1
                continue
        except ZitadelUserMapping.DoesNotExist:
            pass

        email = participant.mail_addr or participant.parent_mail_addr
        if not email:
            modeladmin.message_user(
                request,
                _("%(user)s has no email address – skipping.") % {"user": str(participant)},
                level=messages.WARNING,
            )
            errors += 1
            continue

        existing_user_id = zitadel_client.find_user_by_email(email)
        if existing_user_id:
            ZitadelUserMapping.objects.update_or_create(
                participant=participant,
                defaults={"zitadel_user_id": existing_user_id},
            )
            created += 1
            continue

        user_id, invitation_url = zitadel_client.create_user(
            email=email,
            first_name=participant.first_name,
            last_name=participant.last_name,
            phone=participant.phone or "",
        )
        if user_id:
            ZitadelUserMapping.objects.update_or_create(
                participant=participant,
                defaults={
                    "zitadel_user_id": user_id,
                    "invitation_url": invitation_url or "",
                },
            )
            created += 1
        else:
            modeladmin.message_user(
                request,
                _("Zitadel account creation failed for %(user)s.") % {"user": str(participant)},
                level=messages.ERROR,
            )
            errors += 1

    if created:
        modeladmin.message_user(
            request,
            _("%(count)d Zitadel account(s) provisioned.") % {"count": created},
        )
    if skipped:
        modeladmin.message_user(
            request,
            _("%(count)d participant(s) already had a Zitadel account and were skipped.") % {"count": skipped},
            level=messages.INFO,
        )
    if errors:
        modeladmin.message_user(
            request,
            _("%(count)d error(s) occurred. See warnings above.") % {"count": errors},
            level=messages.ERROR,
        )
