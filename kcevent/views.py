from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import permission_required
from .forms import ParticipantForm, KCEventRegistrationForm
from .models import KCEvent

# allow churches to register their partnership
def managePartnership(request):
    return HttpResponse("Hello, world. You're at the polls index.")

@permission_required('kcevent.Event.can_add')
def listEvents(request):
    return HttpResponse("Yeah lets add event.")

def registerEventLogin(request):
    if request.method == 'POST':
        password = request.POST['password']
        if password == 'mono':
            request.session['is_kclogged_in'] = True
            return redirect(reverse('registerEvent'))
        else:
            return render(request, 'cvjm/kclogin.html', {'error_message': 'Ungültige Zugangsdaten!'})
    else:
        return render(request, 'cvjm/kclogin.html')

def registerEvent(request):
    # first check if user is logged in.
    if not request.session.get('is_kclogged_in', False):
        return registerEventLogin(request)
    # user is logged in. Check if already filled in:
    elif request.session.get('is_kcform_filled', False):
        # user already filled in.
        return render(request, 'cvjm/registrationFinished.html')
    else:
        evt = KCEvent.objects.all()[0]
        form = ParticipantForm(request.POST if request.method == 'POST' else None)
        formReg = KCEventRegistrationForm(
            request.POST if request.method == 'POST' else None,
            request.FILES if request.method == 'POST' else None
        )
        if request.method == 'POST':
            if form.is_valid() and formReg.is_valid():
                form.save()
                formReg.instance.reg_user = form.instance
                formReg.instance.reg_event = evt
                formReg.save()
                request.session['is_kcform_filled'] = True
                return render(request, 'cvjm/registrationFinished.html')
            else:
                for field, errors in form.errors.items():
                    print(field, errors)
                for field, errors in formReg.errors.items():
                    print(field, errors)

        return render(
            request, 'cvjm/registerEvent.html', 
            {
                'form': form,
                'formReg': formReg,
                'evt': evt
            }
    )

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