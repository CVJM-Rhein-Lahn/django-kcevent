from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import permission_required, login_required
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import smart_str
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Subquery, Exists
from django.views.decorators.http import require_http_methods
from .forms import (
    ParticipantForm, 
    KCEventRegistrationForm, 
    EmergencyContactForm, 
    PreviewForm,
    StatisticMatrixForm
)
from .models import (
    KCEvent, KCEventRegistration, PartnerUser, KCEventPartner,
    Participant, Partner
)
from .decorators import event_logged_in
from .wizard import EventRegistrationWizard
import datetime
import zipfile
import io
import os
import csv
import tempfile

# allow churches to register their partnership
def managePartnership(request: WSGIRequest):
    return HttpResponse("Hello, world. You're at the polls index.")


@login_required
@permission_required("kcevent.view_kcevent", raise_exception=True)
def listEvents(request: WSGIRequest):
    # is current logged in user super admin?
    events = None
    if request.user.is_superuser:
        events = KCEvent.objects.all()
    else:
        # get partner orgs.
        partners = Subquery(
            PartnerUser.objects.filter(user=request.user).values("partner")
        )
        events = KCEvent.objects.filter(Exists(partners) | Exists(partners))

    return render(request, "kcevent/events/list.html", {"events": events})


@login_required
@permission_required("kcevent.view_kcevent", raise_exception=True)
def viewEvent(request: WSGIRequest, event_id=None):
    # is current logged in user super admin?
    event = KCEvent.objects.filter(ext_id=event_id).first()
    event_partner = None
    if request.user.is_superuser:
        event_partner = KCEventPartner.objects.filter(evp_event=event)
    else:
        partners = Subquery(
            PartnerUser.objects.filter(user=request.user).values("partner")
        )
        event_partner = KCEventPartner.objects.filter(
            evp_event=event, evp_partner__in=partners
        )

    return render(
        request, "kcevent/events/detail.html", {"event": event, "evp": event_partner}
    )


@login_required
@permission_required("kcevent.view_kcevent", raise_exception=True)
def viewEventParticipants(request: WSGIRequest, event_id=None):
    # is current logged in user super admin?
    event = KCEvent.objects.filter(ext_id=event_id).first()
    participants = None
    partners = None
    if request.user.is_superuser:
        participants = KCEventRegistration.objects.filter(reg_event=event)
    else:
        partners = Subquery(
            PartnerUser.objects.filter(user=request.user).values("partner")
        )
        subquery = Subquery(
            Participant.objects.filter(church__in=partners).values("pk")
        )
        participants = KCEventRegistration.objects.filter(
            reg_event=event, reg_user__in=subquery
        ).order_by("reg_user__last_name", "reg_user__first_name")

    participants = participants.order_by("reg_user__last_name", "reg_user__first_name")

    return render(
        request,
        "kcevent/events/participants.html",
        {"event": event, "participants": participants},
    )

@login_required
@permission_required("kcevent.view_kcevent", raise_exception=True)
def setEventStatistics(request: WSGIRequest, event_id: str, partner_id: str):
    event = KCEvent.objects.get(ext_id=event_id)
    partner = Partner.objects.get(ext_id=partner_id)
    event_partner = KCEventPartner.objects.get(evp_event=event, evp_partner=partner)
    
    if not request.user.is_superuser:
        allowed_partners = PartnerUser.objects.filter(user=request.user, partner=partner)
        if allowed_partners.count() <= 0:
            raise PermissionError('Need proper permission')
    
    data = request.POST if request.POST else None
    form = StatisticMatrixForm(event, event_partner, data=data)
    if request.POST and form.is_valid() and form.has_changed():
        form.save()

    return render(
        request,
        "kcevent/events/statisticsform.html",
        {
            "event": event, "partner": partner, 
            "form": form
        },
    )


@login_required
@permission_required("kcevent.can_download_regdocs", raise_exception=True)
def downloadRegistrationDocuments(request: WSGIRequest, event_url: str):
    # try to find the event
    try:
        evt = KCEvent.objects.get(event_url=event_url)
    except KCEvent.DoesNotExist:
        raise Http404(_("Event not found"))

    # fetch all documents
    registrations = KCEventRegistration.objects.filter(reg_event=evt)
    now = datetime.datetime.now()
    downloadBase = "{0}_{1}".format(now.strftime("%Y_%m_%d"), event_url)
    csvName = "{0}_participants.csv".format(downloadBase)
    zipNameBase = "{0}_documents".format(downloadBase)
    zipName = zipNameBase + ".zip"
    zStream = io.BytesIO()
    zfile = zipfile.ZipFile(zStream, mode="x")
    # create a document which all participants information - usable as CSV
    regtmp = tempfile.NamedTemporaryFile(delete=False)
    regtmp.close()
    csvfile = open(regtmp.name, "w", encoding="utf-8", newline="")
    rtw = csv.writer(csvfile, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    headerFields = [
        _("Surname"),
        _("First name"),
        _("Street"),
        _("House no."),
        _("Postal code"),
        _("City"),
        _("Phone"),
        _("Mail address"),
        _("Birthday"),
        _("Church"),
        _("Intolerances"),
        _("Nutrition"),
        _("Lactose intolerance"),
        _("Celiac disease"),
        _("Role"),
        _("Gender"),
        _("Notes"),
        _("Additional form data"),
        _("Event passport"),
        _("Medical dispense"),
        _("Consent form"),
    ]
    rtw.writerow(headerFields)
    for r in registrations:
        user_name = smart_str(
            r.reg_user.last_name.lower().replace(" ", "")
            + "_"
            + r.reg_user.first_name.lower().replace(" ", "")
        ) + "_{0}".format(r.reg_user.id)
        # Doc pass
        arcPathDocPass = ""
        if r.reg_doc_pass:
            arcPathDocPass = os.path.join(
                zipNameBase, user_name, os.path.basename(r.reg_doc_pass.name)
            )
            try:
                zfile.write(
                    os.path.join(settings.MEDIA_ROOT, r.reg_doc_pass.name),
                    arcPathDocPass,
                )
            except FileNotFoundError:
                zfile.writestr(arcPathDocPass, "File not found on server.")
                pass
        # Medidispense
        arcPathMediDispense = ""
        if r.reg_doc_meddispense:
            arcPathMediDispense = os.path.join(
                zipNameBase, user_name, os.path.basename(r.reg_doc_meddispense.name)
            )
            try:
                zfile.write(
                    os.path.join(settings.MEDIA_ROOT, r.reg_doc_meddispense.name),
                    arcPathMediDispense,
                )
            except FileNotFoundError:
                zfile.writestr(arcPathMediDispense, "File not found on server.")
                pass
        # Consent
        arcPathConsent = ""
        if r.reg_doc_consent:
            arcPathConsent = os.path.join(
                zipNameBase, user_name, os.path.basename(r.reg_doc_consent.name)
            )
            try:
                zfile.write(
                    os.path.join(settings.MEDIA_ROOT, r.reg_doc_consent.name),
                    arcPathConsent,
                )
            except FileNotFoundError:
                zfile.writestr(arcPathConsent, "File not found on server.")
                pass

        rp = r.reg_user
        rtw.writerow(
            [
                rp.last_name,
                rp.first_name,
                rp.street,
                rp.house_number,
                rp.zip_code,
                rp.city,
                rp.phone,
                rp.mail_addr,
                rp.birthday.strftime("%d.%m.%Y"),
                rp.church.name,
                rp.intolerances,
                rp.get_nutrition_display(),
                _("Yes") if rp.lactose_intolerance else _("No"),
                _("Yes") if rp.celiac_disease else _("No"),
                rp.role,
                rp.get_gender_display(),
                r.reg_notes,
                r.reg_adddata,
                # documents
                arcPathDocPass,
                arcPathMediDispense,
                arcPathConsent,
            ]
        )

    csvfile.close()
    zfile.write(regtmp.name, csvName)
    zfile.close()
    zStream.seek(0)
    os.unlink(regtmp.name)
    response = HttpResponse(zStream, content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=%s" % smart_str(zipName)
    return response


def registerEventLogin(
    request: WSGIRequest, event_url: str, evt: KCEvent | None = None
):
    if not evt:
        # try to find the event
        try:
            evt = KCEvent.objects.get(event_url=event_url)
        except KCEvent.DoesNotExist:
            raise Http404(_("Event not found"))

    if request.method == "POST":
        password = None
        try:
            password = request.POST["password"]
        except KeyError:
            pass

        if password == evt.reg_pwd:
            request.session["is_kclogged_in_" + str(evt.id)] = True
            request.session[f"is_kclogged_in_{str(evt.id)}_login"] = (
                datetime.datetime.now().isoformat()
            )
            return redirect(
                reverse("registerEvent", kwargs={"event_url": evt.event_url})
            )
        else:
            return render(
                request,
                "cvjm/kclogin.html",
                {
                    "error_message": _("Invalid credentials provided!"),
                    "evt": evt,
                    "loginUrl": reverse(
                        "registerEventLogin", kwargs={"event_url": evt.event_url}
                    ),
                },
            )
    elif evt.reg_pwd:
        return render(
            request,
            "cvjm/kclogin.html",
            {
                "evt": evt,
                "loginUrl": reverse(
                    "registerEventLogin", kwargs={"event_url": evt.event_url}
                ),
            },
        )
    else:
        request.session["is_kclogged_in_" + str(evt.id)] = True
        request.session[f"is_kclogged_in_{str(evt.id)}_login"] = (
            datetime.datetime.now().isoformat()
        )
        return redirect(reverse("registerEvent", kwargs={"event_url": evt.event_url}))

@require_http_methods(["GET", "POST"])
@event_logged_in(registerEventLogin)
def registerEvent(request: WSGIRequest, event_url: str, evt: KCEvent | None = None):
    form_list = [
        ('pd', ParticipantForm),
        ('rd', KCEventRegistrationForm)
    ]
    if evt.enableEmergencyContacts:
        form_list.append(
            ('ec', EmergencyContactForm)
        )
    # Dummy form
    form_list.append(
        ('review', PreviewForm)
    )
        
    initial = {}
    wiz = EventRegistrationWizard.as_view(evt, form_list, initial_dict=initial)(request)
    return wiz


def listPublicEvents(request: WSGIRequest):
    # check which event is online...
    now = datetime.datetime.now()
    events = KCEvent.objects.filter(
        registration_start__lte=now, registration_end__gte=now
    ).order_by("registration_start")
    if not events:
        return redirect(settings.MAIN_PAGE)
    elif len(events) > 1:
        # No post data availabe, let's just show the page to list the available
        # events for registration.
        return render(request, "cvjm/listEvent.html", {"events": events})
    else:
        # take the first active one
        return redirect(
            reverse("registerEvent", kwargs={"event_url": events[0].event_url})
        )


def user_login(request: WSGIRequest):
    if request.method == "POST":
        # Process the request if posted data are available
        username = request.POST["username"]
        password = request.POST["password"]

        # Check username and password combination if correct
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # Save session as cookie to login the user
                login(request, user)
                # Success, now let's login the user.
                if request.GET.get("next"):
                    return redirect(request.GET.get("next"))
                else:
                    return render(request, "kcevent/account.html")
            else:
                return render(
                    request,
                    "kcevent/login.html",
                    {"error_message": "User account is disabled."},
                )
        else:
            # Incorrect credentials, let's throw an error to the screen.
            return render(
                request,
                "kcevent/login.html",
                {"error_message": "Incorrect username and / or password."},
            )
    else:
        # No post data availabe, let's just show the page to the user.
        return render(request, "kcevent/login.html")


def responseError400(request: WSGIRequest, exception):
    return _responseError(400, request, exception)


def responseError403(request: WSGIRequest, exception):
    return _responseError(403, request, exception)


def responseError404(request: WSGIRequest, exception):
    return _responseError(404, request, exception)


def responseError500(request: WSGIRequest):
    return _responseError(500, request)


def _responseError(statusCode: int, request: WSGIRequest, exception=None):
    # No post data availabe, let's just show the page to the user.
    return render(request, "cvjm/error.html", {"error_code": statusCode})

    