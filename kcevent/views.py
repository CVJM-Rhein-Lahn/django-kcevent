from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import permission_required, login_required
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import smart_str
from .forms import ParticipantForm, KCEventRegistrationForm
from .models import KCEvent, KCEventRegistration, Partner
from .formhelper import KcFormHelper
from sentry_sdk import configure_scope as sentry_scope
from sentry_sdk import capture_exception
import datetime
import zipfile
import io
import os
import csv
import tempfile

# allow churches to register their partnership
def managePartnership(request):
    return HttpResponse("Hello, world. You're at the polls index.")

@permission_required('kcevent.Event.can_add')
def listEvents(request):
    return HttpResponse("Yeah lets add event.")

@login_required
@permission_required('kcevent.can_download_regdocs', raise_exception=True)
def downloadRegistrationDocuments(request, event_url):
    # try to find the event
    try:
        evt = KCEvent.objects.get(event_url=event_url)
    except:
        raise Http404(_('Event not found'))

    # fetch all documents
    registrations = KCEventRegistration.objects.filter(reg_event=evt)
    now = datetime.datetime.now()
    downloadBase = '{0}_{1}'.format(
        now.strftime('%Y_%m_%d'), event_url
    )
    csvName = '{0}_participants.csv'.format(downloadBase)
    zipNameBase = '{0}_documents'.format(downloadBase)
    zipName = zipNameBase + '.zip'
    zStream = io.BytesIO()
    zfile = zipfile.ZipFile(zStream, mode='x')
    # create a document which all participants information - usable as CSV
    regtmp = tempfile.NamedTemporaryFile(delete=False)
    regtmp.close()
    csvfile = open(regtmp.name, 'w', encoding='iso-8859-1', newline='')
    rtw = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    headerFields = [
        _('Surname'), _('First name'), _('Street'), _('House no.'), _('Postal code'),
        _('City'), _('Phone'), _('Mail address'), _('Birthday'), _('Church'),
        _('Intolerances'), _('Nutrition'), _('Lactose intolerance'), 
        _('Celiac disease'), _('Role'), _('Gender'),
        _('Notes'), _('Event passport'), _('Medical dispense'), _('Consent form')
    ]
    rtw.writerow(headerFields)
    for r in registrations:
        user_name = smart_str(r.reg_user.last_name.lower().replace(' ', '') + '_' + \
            r.reg_user.first_name.lower().replace(' ', '')) + \
            '_{0}'.format(r.reg_user.id)
        # Doc pass
        arcPathDocPass = ''
        if r.reg_doc_pass:
            arcPathDocPass = os.path.join(zipNameBase, user_name, os.path.basename(r.reg_doc_pass.name))
            try:
                zfile.write(os.path.join(settings.MEDIA_ROOT, r.reg_doc_pass.name), arcPathDocPass)
            except FileNotFoundError:
                zfile.writestr(arcPathDocPass, 'File not found on server.')
                pass
        # Medidispense
        arcPathMediDispense = ''
        if r.reg_doc_meddispense:
            arcPathMediDispense = os.path.join(zipNameBase, user_name, os.path.basename(r.reg_doc_meddispense.name))
            try:
                zfile.write(os.path.join(settings.MEDIA_ROOT, r.reg_doc_meddispense.name), arcPathMediDispense)
            except FileNotFoundError:
                zfile.writestr(arcPathMediDispense, 'File not found on server.')
                pass
        # Consent
        arcPathConsent = ''
        if r.reg_doc_consent:
            arcPathConsent = os.path.join(zipNameBase, user_name, os.path.basename(r.reg_doc_consent.name))
            try:
                zfile.write(os.path.join(settings.MEDIA_ROOT, r.reg_doc_consent.name), arcPathConsent)
            except FileNotFoundError:
                zfile.writestr(arcPathConsent, 'File not found on server.')
                pass
    
        rp = r.reg_user
        rtw.writerow([
            rp.last_name, rp.first_name, rp.street, rp.house_number,
            rp.zip_code, rp.city, rp.phone, rp.mail_addr, 
            rp.birthday.strftime('%d.%m.%Y'),
            rp.church.name, rp.intolerances, rp.get_nutrition_display(),
            _('Yes') if rp.lactose_intolerance else _('No'), 
            _('Yes') if rp.celiac_disease else _('No'),
            rp.get_role_display(), rp.get_gender_display(),
            r.reg_notes,
            # documents
            arcPathDocPass, arcPathMediDispense, arcPathConsent
        ])

    csvfile.close()
    zfile.write(regtmp.name, csvName)
    zfile.close()
    zStream.seek(0)
    os.unlink(regtmp.name)
    response = HttpResponse(zStream, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(zipName)
    return response

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
    with sentry_scope() as scope:
        scope.set_tag('event.slug', event_url)
        
    # try to find the event
    try:
        evt = KCEvent.objects.get(event_url=event_url)
    except:
        raise Http404(_('Event not found'))

    with sentry_scope() as scope:
        scope.set_tag('event.id', evt.id)

    # first check if user is logged in.
    if not request.session.get('is_kclogged_in_' + str(evt.id), False):
        return registerEventLogin(request, event_url, evt)
    else:
        # FIXME: depending on the given user data (first name, last name, birthday, etc.) identify and update
        # existing user!
        kfh = KcFormHelper.checkInstantiate(request, evt, form=ParticipantForm, formReg=KCEventRegistrationForm)
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
                    try:
                        kfh.formReg.instance.sendConfirmation(request)
                    except Exception as e:
                        # catch SMTP issues, but log it!
                        # for user experience, just continue!
                        capture_exception(e)
                    # send information to host and church
                    try:
                        kfh.formReg.instance.notifyHostChurch(request)
                    except Exception as e:
                        # catch SMTP issues, but log it!
                        # for user experience, just continue!
                        capture_exception(e)
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
            elif request.POST.get('confirm', 'no') != 'no' and kfh.getStage() == 'confirm':
                raise Exception("Error validating event registration.")
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

        # Check username and password combination if correct
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # Save session as cookie to login the user
                login(request, user)
                # Success, now let's login the user.
                if request.GET.get('next'):
                    return redirect(request.GET.get('next'))
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

def responseError400(request, exception):
    return _responseError(400, request, exception)

def responseError403(request, exception):
    return _responseError(403, request, exception)

def responseError404(request, exception):
    return _responseError(404, request, exception)

def responseError500(request):
    return _responseError(500, request)

def _responseError(statusCode, request, exception=None):
    # No post data availabe, let's just show the page to the user.
    return render(request, 'cvjm/error.html', {'error_code': statusCode})
