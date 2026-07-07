import logging
import os
from collections import OrderedDict
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.utils.decorators import classonlymethod
from formtools.wizard.views import SessionWizardView #, CookieWizardView
from formtools.wizard.forms import ManagementForm
from sentry_sdk import capture_exception
from .models import (
    KCEvent,
    KCEventRegistration,
    KCEventRegistrationStateTypes,
    Participant,
    ZitadelUserMapping,
)
from . import zitadel_client

logger = logging.getLogger(__name__)

class EventRegistrationWizard(SessionWizardView):
    file_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, "kcevent")
    )
    
    event: KCEvent | None = None

    completed_registrations: list[int] = []

    def __init__(self, event: KCEvent | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        self.completed_registrations = []
        
    def __repr__(self):
        return f'<{self.__class__.__name__}: forms: {self.form_list}>'
    
    def get_context_data(self, form, **kwargs):
        data = super().get_context_data(form=form, **kwargs)
        data['wizard']['event'] = self.event
        if not self.completed_registrations:
            self.completed_registrations = self.request.session.get('completed_registrations', [])
        if self.completed_registrations:
            data['wizard']['completed_registrations'] = [
                KCEventRegistration.objects.get(id=rid)
                for rid in self.completed_registrations
                if KCEventRegistration.objects.filter(id=rid).exists()
            ]
        return data
    
    def get_form_initial(self, step):
        data = super().get_form_initial(step)
        if step == 'rd' or step == 'review':
            reg_user = self.get_form_instance('pd')
            if reg_user is None:
                reg_user_id = (self.storage.extra_data or {}).get('pd')
                if reg_user_id:
                    reg_user = Participant.objects.get(id=reg_user_id)
            data['reg_event'] = self.event
            data['reg_user'] = reg_user

        if step == 'pd':
            prefill = (self.storage.extra_data or {}).get('pd_prefill')
            if prefill:
                data.update(prefill)

        return data
    
    def get_form_instance(self, step):
        data = super().get_form_instance(step)
        extra = self.storage.extra_data or {}
        if step == 'pd' and data is None:
            reg_user_id = extra.get('pd')
            if reg_user_id:
                data = Participant.objects.get(id=reg_user_id)
        if step == 'rd' and data is None:
            reg_id = extra.get('rd')
            if reg_id:
                data = KCEventRegistration.objects.get(id=reg_id)
            else:
                reg_user = self.get_form_instance('pd')
                if reg_user is None:
                    reg_user_id = extra.get('pd')
                    if reg_user_id:
                        reg_user = Participant.objects.get(id=reg_user_id)
                data = KCEventRegistration(reg_user=reg_user, reg_event=self.event)

        return data
        
    @classonlymethod
    def as_view(cls, event: KCEvent, *args, **kwargs):
        cls = super().as_view(*args, event=event, **kwargs)
        return cls

    def get_form_kwargs(self, step=None):
        data = super().get_form_kwargs(step)
        data['event'] = self.event
        if step == 'review':
            final_forms = OrderedDict()
            # walk through the form list and try to validate the data again.
            for form_key in self.get_form_list():
                if form_key != step:
                    form_obj = self.get_form(
                        step=form_key,
                        data=self.storage.get_step_data(form_key),
                        files=self.storage.get_step_files(form_key)
                    )
                    #if not form_obj.is_valid():
                    #    return self.render_revalidation_failure(form_key, form_obj, **kwargs)
                    final_forms[form_key] = form_obj
                    
            data['form_list'] = final_forms
        
        return data
        
    def render_next_step(self, form, **kwargs):
        # save the form.
        form.save()
        self.instance_dict[self.steps.current] = form.instance
        self.add_extra_data(self.steps.current, form.instance.id)
        return super().render_next_step(form, **kwargs)

    def _persist_extra_data(self, extra: dict) -> None:
        try:
            prefix = getattr(self.storage, "prefix", None)
            if not prefix:
                return
            wizard_data = self.request.session.get(prefix, {}) or {}
            wizard_data["extra_data"] = dict(extra)
            self.request.session[prefix] = wizard_data
            self.request.session.modified = True
        except Exception:
            logger.exception("Failed to persist wizard extra_data in session")
    
    def add_extra_data(self, step, data):
        extra_data = self.storage.extra_data
        if extra_data is None:
            extra_data = {}
        extra_data[step] = data
        self.storage.extra_data = extra_data

    def post(self, *args, **kwargs):
        """Intercept special wizard actions from the review step."""
        # extract / store the completed registrations from the session
        self.completed_registrations = self.request.session.get('completed_registrations', [])
        if self.steps.current == 'review':
            if self.request.POST.get('_add_another'):
                return self._handle_add_another()
            if self.request.POST.get('_cancel_last'):
                return self._handle_cancel_last()
            if self.request.POST.get('_final_confirm'):
                return self.done([], {})
            if 'confirm' in self.request.POST:
                if self.completed_registrations:
                    self.request.session['completed_registrations'] = self.completed_registrations
                    return self._render_allreview()
        response = super().post(*args, **kwargs)
        self.request.session['completed_registrations'] = self.completed_registrations
        return response

    def _render_allreview(self):
        """Render the final overview page listing all pending registrations."""
        earlier_regs = []
        for rid in self.completed_registrations:
            try:
                earlier_regs.append(KCEventRegistration.objects.get(id=rid))
            except KCEventRegistration.DoesNotExist:
                pass

        rd_id = self.storage.extra_data.get('rd')
        current_reg = None
        if rd_id:
            try:
                current_reg = KCEventRegistration.objects.get(id=rd_id)
            except KCEventRegistration.DoesNotExist:
                pass

        all_pending = ([current_reg] if current_reg else []) + earlier_regs

        return render(
            self.request,
            "cvjm/wizard/allreview.html",
            {
                "wizard": {
                    "management_form": ManagementForm(prefix=self.prefix, initial={
                        'current_step': self.steps.current,
                    }),
                    "steps": self.steps,
                    "event": self.event,
                    "all_pending": all_pending,
                }
            },
        )

    def render(self, form=None, **kwargs):
        response = super().render(form=form, **kwargs)
        current_form = form or self.get_form()
        if current_form.is_bound and not current_form.is_valid():
            logger.warning(
                "Wizard step '%s' has validation errors: %s",
                self.steps.current,
                current_form.errors,
            )
        return response

    def _handle_add_another(self):
        """Store current registration as draft, reset wizard for next child."""
        extra = self.storage.extra_data or {}
        rd_id = extra.get('rd')
        pd_id = extra.get('pd')

        if rd_id:
            try:
                reg = KCEventRegistration.objects.get(id=rd_id)
                # keep status as incomplete (draft), do NOT send confirmation yet
                reg.reg_status = KCEventRegistrationStateTypes.REGTYPE_INCOMPLETE
                reg.save()

                if rd_id not in self.completed_registrations:
                    self.completed_registrations.append(rd_id)
            except KCEventRegistration.DoesNotExist:
                pass

        prefill = {}
        prev = None
        if pd_id:
            try:
                prev = Participant.objects.get(id=pd_id)
                prefill = {
                    'street': prev.street,
                    'house_number': prev.house_number,
                    'zip_code': prev.zip_code,
                    'city': prev.city,
                    'church': prev.church_id,
                    'role': prev.role_id,
                    'parent_mail_addr': prev.parent_mail_addr,
                }
                self.request.session['pd_prefill'] = prefill
            except Participant.DoesNotExist:
                pass

        extra['pd_prefill'] = prefill
        extra.pop('pd', None)
        extra.pop('rd', None)

        self.storage.reset()
        self.storage.extra_data = dict(extra)
        self._persist_extra_data(extra)

        return redirect(
            reverse('registerEvent', kwargs={'event_url': self.event.event_url})
        )

    def _handle_cancel_last(self):
        """Discard current (last) draft registration and return to the overview."""
        extra = self.storage.extra_data or {}
        rd_id = extra.get('rd')

        if rd_id:
            try:
                reg = KCEventRegistration.objects.get(id=rd_id)
                reg.delete()
            except KCEventRegistration.DoesNotExist:
                pass
            extra.pop('rd', None)
            extra.pop('pd', None)

        if self.completed_registrations:
            extra.pop('pd_prefill', None)

        self.storage.extra_data = extra
        self._persist_extra_data(extra)
        return redirect(
            reverse('registerEvent', kwargs={'event_url': self.event.event_url})
        )

    def _finalize_registration(self, reg: KCEventRegistration):
        """Mark registration complete, provision Zitadel account and send emails."""
        reg.setRegistrationComplete()
        reg.save()
        self._provision_zitadel_account(reg)
        try:
            reg.sendConfirmation()
        except Exception as e:
            capture_exception(e)
        try:
            reg.notifyHostChurch()
        except Exception as e:
            capture_exception(e)
    
    def get_template_names(self):
        if self.steps.current == 'review':
            return os.path.join('cvjm', 'wizard', 'preview.html')
        else:
            return os.path.join('cvjm', 'wizard', 'form.html')

    def done(self, form_list, form_dict, **kwargs):
        final_forms = OrderedDict()
        current_reg = None
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key)
            )
            if form_key == 'rd':
                current_reg = form_obj.instance

            final_forms[form_key] = form_obj

        earlier_regs = []
        for rid in self.completed_registrations:
            try:
                earlier_regs.append(KCEventRegistration.objects.get(id=rid))
            except KCEventRegistration.DoesNotExist:
                pass

        # finalize all registrations together at the very end
        all_regs = ([current_reg] if current_reg else []) + earlier_regs
        for reg in all_regs:
            self._finalize_registration(reg)

        self.request.session.pop('completed_registrations', None)

        return render(
            self.request,
            "cvjm/wizard/done.html",
            {
                "wizard": {
                    "form_data": final_forms,
                    "steps": self.steps,
                    "event": self.event,
                    "current_registration": current_reg,
                    "earlier_registrations": earlier_regs,
                    "all_registrations": all_regs,
                }
            },
        )

    def _provision_zitadel_account(self, registration: KCEventRegistration):
        """Create a Zitadel user account for the participant if one does not exist yet."""
        participant = registration.reg_user
        try:
            existing = participant.zitadel_mapping
            if existing.zitadel_user_id:
                return
        except ZitadelUserMapping.DoesNotExist:
            pass

        email = participant.mail_addr or participant.parent_mail_addr
        if not email:
            logger.warning(
                "Participant %s has no email - skipping Zitadel account creation.",
                participant.id,
            )
            return

        existing_user_id = zitadel_client.find_user_by_email(email)
        if existing_user_id:
            ZitadelUserMapping.objects.update_or_create(
                participant=participant,
                defaults={"zitadel_user_id": existing_user_id},
            )
            return

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
        else:
            logger.error(
                "Zitadel account creation failed for participant %s.", participant.id
            )
