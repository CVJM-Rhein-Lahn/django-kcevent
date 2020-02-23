from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import permission_required
from django.utils.translation import ugettext_lazy as _
from .forms import ParticipantForm, KCEventRegistrationForm
from .models import KCEvent, Partner
from .formhelper import KcFormHelper
import datetime

# allow churches to register their partnership
def managePartnership(request):
    return HttpResponse("Hello, world. You're at the polls index.")

@permission_required('kcevent.Event.can_add')
def listEvents(request):
    return HttpResponse("Yeah lets add event.")

def registerEventLogin(request, event_url, evt=None):
    if not evt:
        # try to find the event
        try:
            evt = KCEvent.objects.get(event_url=event_url)
        except:
            raise Http404(_('Event not found'))

    if request.method == 'POST':
        password = request.POST['password']
        if password == evt.reg_pwd:
            request.session['is_kclogged_in_' + str(evt.id)] = True
            return redirect(reverse('registerEvent', kwargs={'event_url': evt.event_url}))
        else:
            return render(
                request, 'cvjm/kclogin.html', 
                {
                'error_message': _('Invalid credentials provided!'),
                'evt': evt,
                'loginUrl': reverse('registerEventLogin', kwargs={'event_url': evt.event_url})
                }
            )
    elif evt.reg_pwd:
        print(reverse('registerEventLogin', kwargs={'event_url': evt.event_url}))
        return render(
            request, 'cvjm/kclogin.html',
            {
                'evt': evt,
                'loginUrl': reverse('registerEventLogin', kwargs={'event_url': evt.event_url})
            }
        )
    else:
        request.session['is_kclogged_in_' + str(evt.id)] = True
        return redirect(reverse('registerEvent', kwargs={'event_url': evt.event_url}))

def registerEvent(request, event_url):
    # try to find the event
    try:
        evt = KCEvent.objects.get(event_url=event_url)
    except:
        raise Http404(_('Event not found'))

    # first check if user is logged in.
    if not request.session.get('is_kclogged_in_' + str(evt.id), False):
        return registerEventLogin(request, event_url, evt)
    else:
        # FIXME: depending on the given user data (first name, last name, birthday, etc.) identify and update
        # existing user!
        kfh = KcFormHelper.checkInstantiate(request, form=ParticipantForm, formReg=KCEventRegistrationForm)
        if request.method == 'POST':
            kfh.formReg.instance.reg_user = kfh.form.instance
            kfh.formReg.instance.reg_event = evt
            if kfh.isValid():
                if request.POST.get('confirm', 'no') != 'no' and kfh.getStage() == 'confirm':
                    kfh.form.save()
                    kfh.formReg.instance.reg_user = kfh.form.instance
                    kfh.formReg.instance.reg_event = evt
                    kfh.formReg.save()
                    kfh.formReg.instance.updateFilePaths()
                    kfh.clean()
                    partner = Partner.objects.get(id=kfh.form.instance.church.id)
                    # send confirmation to participant
                    kfh.formReg.instance.sendConfirmation()
                    # send information to host and church
                    kfh.formReg.instance.notifyHostChurch()
                    return render(
                        request, 'cvjm/registrationFinished.html',
                        {
                            'evt': evt,
                            'partner': partner,
                            'kfh': kfh
                        }
                    )
                elif request.POST.get('edit', None) is None:
                    kfh.setStage('preview')
                    # fetch the corresponding objects.
                    partner = Partner.objects.get(id=kfh.form.instance.church.id)
                    return render(
                        request, 'cvjm/registerEventConfirm.html', 
                        {
                            'evt': evt,
                            'partner': partner,
                            'kfh': kfh,
                            'registerUrl': reverse('registerEvent', kwargs={'event_url': evt.event_url})
                        }
                    )
        kfh.setStage(None)
        return render(
            request, 'cvjm/registerEvent.html', 
            {
                'evt': evt,
                'kfh': kfh,
                'registerUrl': reverse('registerEvent', kwargs={'event_url': evt.event_url})
            }
        )

def listPublicEvents(request):
    # check which event is online...
    now = datetime.datetime.now()
    events = KCEvent.objects.filter(registration_start__lte=now, registration_end__gte=now)
    if not events:
        return redirect(settings.MAIN_PAGE)
    else:
        # take the first active one
        return redirect(reverse('registerEvent', kwargs={'event_url': events[0].event_url}))

def user_login(request):
    if request.method == 'POST':
        # Process the request if posted data are available
        username = request.POST['username']
        password = request.POST['password']
        nextPage
        # Check username and password combination if correct
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # Save session as cookie to login the user
                login(request, user)
                # Success, now let's login the user.
                if self.request.GET.get('next'):
                    return redirect(self.request.GET.get('next'))
                else:
                    return render(request, 'kcevent/account.html')
            else:
                return render(request, 'kcevent/login.html', {'error_message': 'User account is disabled.'})
        else:
            # Incorrect credentials, let's throw an error to the screen.
            return render(request, 'kcevent/login.html', {'error_message': 'Incorrect username and / or password.'})
    else:
        # No post data availabe, let's just show the page to the user.
        return render(request, 'kcevent/login.html')