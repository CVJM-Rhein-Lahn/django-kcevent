import os
from collections import OrderedDict
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.decorators import classonlymethod
from django.utils import timezone
from formtools.wizard.views import SessionWizardView #, CookieWizardView
import sentry_sdk
from sentry_sdk import capture_exception
from .models import KCEvent, KCEventRegistration, Participant

class EventRegistrationWizard(SessionWizardView):
    file_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, "kcevent")
    )
    
    event: KCEvent | None = None

    def __init__(self, event: KCEvent | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        
    def __repr__(self):
        return f'<{self.__class__.__name__}: forms: {self.form_list}>'
    
    def get_context_data(self, form, **kwargs):
        data = super().get_context_data(form=form, **kwargs)
        data['wizard']['event'] = self.event
        
        return data
    
    def get_form_initial(self, step):
        data = super().get_form_initial(step)
        if step == 'rd' or step == 'review':
            reg_user = self.get_form_instance('pd')
            if reg_user is None:
                reg_user_id = self.storage.extra_data.get('pd')
                if reg_user_id:
                    reg_user = Participant.objects.get(id=reg_user_id)
            data['reg_event'] = self.event
            data['reg_user'] = reg_user
            
        return data
    
    def get_form_instance(self, step):
        data = super().get_form_instance(step)
        if step == 'pd' and data is None:
            reg_user_id = self.storage.extra_data.get('pd')
            if reg_user_id:
                    data = Participant.objects.get(id=reg_user_id)
        if step == 'rd' and data is None:
            reg_id = self.storage.extra_data.get('rd')
            if reg_id:
                data = KCEventRegistration.objects.get(id=reg_id)
            else:
                reg_user = self.get_form_instance('pd')
                if reg_user is None:
                    reg_user_id = self.storage.extra_data.get('pd')
                    if reg_user_id:
                        reg_user = Participant.objects.get(id=reg_user_id)
                data = KCEventRegistration(reg_user=reg_user, reg_event=self.event)
        
        return data
        
    @classonlymethod
    def as_view(cls, event: KCEvent, *args, **kwargs):
        return super().as_view(*args, event=event, **kwargs)

    HISTORY_SIZE = 10

    def _trace(self, action):
        """Attach the wizard state and a per-session step history to Sentry events."""
        extra_data = self.storage.extra_data or {}
        state = {
            'action': action,
            'stored_step': self.storage.current_step,
            'posted_step': self.request.POST.get(f'{self.prefix}-current_step'),
            'goto_step': self.request.POST.get('wizard_goto_step'),
            'steps_with_data': sorted(self.storage.data.get(self.storage.step_data_key, {})),
            'saved_objects': sorted(extra_data),
            'has_participant': bool(extra_data.get('pd')),
            'time': timezone.now().isoformat(),
        }
        sentry_sdk.set_tag('wizard.step', state['posted_step'] or state['stored_step'])
        sentry_sdk.set_tag('wizard.action', action)
        sentry_sdk.set_context('wizard', state)

        # Kept outside the wizard storage, so it survives storage resets.
        history_key = f'{self.prefix}_history_{self.event.id if self.event else ""}'
        history = self.request.session.get(history_key, [])[-(self.HISTORY_SIZE - 1):]
        history.append(state)
        self.request.session[history_key] = history
        sentry_sdk.set_context('wizard.history', {'entries': history})

    def get(self, *args, **kwargs):
        # Note: formtools resets the wizard storage on every GET.
        self._trace('get')
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._trace('post')
        # The wizard storage may have been reset (e.g. registration opened in
        # another tab or already finished) while an old page is still open.
        # Without a stored participant, later steps cannot be processed.
        target_step = self.request.POST.get('wizard_goto_step') or self.request.POST.get(
            f'{self.prefix}-current_step'
        )
        participant_id = (self.storage.extra_data or {}).get('pd')
        if target_step and target_step != self.steps.first and not participant_id:
            self._trace('restart_missing_participant')
            self.storage.reset()
            self.storage.current_step = self.steps.first
            return self.render(self.get_form(), session_expired=True)

        return super().post(*args, **kwargs)

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
    
    def add_extra_data(self, step, data): 
        extra_data = self.storage.extra_data
        if extra_data is None:
            extra_data = {}
        extra_data[self.steps.current] = data
        self.storage.extra_data = extra_data
    
    def get_template_names(self):
        if self.steps.current == 'review':
            return os.path.join('cvjm', 'wizard', 'preview.html')
        else:
            return os.path.join('cvjm', 'wizard', 'form.html')

    def done(self, form_list, form_dict, **kwargs):
        self._trace('done')
        final_forms = OrderedDict()
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key)
            )
            # mark registration as complete
            if form_key == 'rd':
                form_obj.instance.setRegistrationComplete()
                form_obj.save()
                # send confirmation to participant
                try:
                    form_obj.instance.sendConfirmation()
                except Exception as e:
                    # catch SMTP issues, but log it!
                    # for user experience, just continue!
                    capture_exception(e)
                
                # send information to host and church
                try:
                    form_obj.instance.notifyHostChurch()
                except Exception as e:
                    # catch SMTP issues, but log it!
                    # for user experience, just continue!
                    capture_exception(e)
            
            final_forms[form_key] = form_obj

        form_data = final_forms
        return render(
            self.request,
            "cvjm/wizard/done.html",
            {
                "wizard": {
                    "form_data": form_data,
                    "steps": self.steps,
                    "event": self.event
                }
            },
        )
