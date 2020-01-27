from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import permission_required

# allow churches to register their partnership
def managePartnership(request):
    return HttpResponse("Hello, world. You're at the polls index.")

@permission_required('kcevent.Event.can_add')
def listEvents(request):
    return HttpResponse("Yeah lets add event.")

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