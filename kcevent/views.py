from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import permission_required
from django.utils.translation import ugettext_lazy as _
from .forms import ParticipantForm, KCEventRegistrationForm
from .models import KCEvent, Partner
import uuid, json

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
                'event': evt,
                'loginUrl': reverse('registerEventLogin', kwargs={'event_url': evt.event_url})
                }
            )
    elif evt.reg_pwd:
        print(reverse('registerEventLogin', kwargs={'event_url': evt.event_url}))
        return render(
            request, 'cvjm/kclogin.html',
            {
                'event': evt,
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
    # user is logged in. Check if already filled in:
    elif request.session.get('is_kcform_filled_' + str(evt.id), False):
        # user already filled in.
        return render(request, 'cvjm/registrationFinished.html')
    else:
        formUuid = None
        editConfirm = False
        if request.method == 'POST' and request.POST.get('fh', None) and \
            (request.POST.get('confirm', None) != None or request.POST.get('edit', None) != None):
            formUuid = request.POST.get('fh')
            form = ParticipantForm(json.loads(request.session['f_' + formUuid]))
            formReg = KCEventRegistrationForm(json.loads(request.session['f_' + formUuid]))
            editConfirm = True
        else:
            formUuid = str(uuid.uuid4())
            form = ParticipantForm(request.POST if request.method == 'POST' else None)
            formReg = KCEventRegistrationForm(
                request.POST if request.method == 'POST' else None,
                request.FILES if request.method == 'POST' else None
            )

        if request.method == 'POST':
            if form.is_valid() and formReg.is_valid():
                if request.POST.get('confirm', None):
                    form.save()
                    formReg.instance.reg_user = form.instance
                    formReg.instance.reg_event = evt
                    formReg.save()
                    request.session['is_kcform_filled_' + str(evt.id)] = True
                    del(request.session['f_' + formUuid])
                    return render(request, 'cvjm/registrationFinished.html')
                elif not editConfirm:
                    request.session['f_' + formUuid] = json.dumps(request.POST)
                    # fetch the corresponding objects.
                    partner = Partner.objects.get(id=form.instance.church.id)
                    print(formReg.instance.reg_doc_pass.url)
                    return render(
                        request, 'cvjm/registerEventConfirm.html', 
                        {
                            'form': form,
                            'formReg': formReg,
                            'evt': evt,
                            'partner': partner,
                            'fh': formUuid,
                            'registerUrl': reverse('registerEvent', kwargs={'event_url': evt.event_url})
                        }
                    )
        return render(
            request, 'cvjm/registerEvent.html', 
            {
                'form': form,
                'formReg': formReg,
                'evt': evt,
                'fh': formUuid,
                'registerUrl': reverse('registerEvent', kwargs={'event_url': evt.event_url})
            }
        )

def listPublicEvents(request):
    pass

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