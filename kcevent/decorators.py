import datetime
from sentry_sdk import configure_scope as sentry_scope
from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from .models import KCEvent

def event_logged_in(registerEventLogin = None):
    def decorator(view_func):
        def wrapper(request: WSGIRequest, event_url: str, *args, **kwargs):
            with sentry_scope() as scope:
                scope.set_tag("event.slug", event_url)
                
            # try to find the event
            try:
                evt: KCEvent = KCEvent.objects.get(event_url=event_url)
            except KCEvent.DoesNotExist:
                raise Http404(_("Event not found"))

            with sentry_scope() as scope:
                scope.set_tag("event.id", evt.id)

            fallbackExpiration = (
                datetime.datetime.now() - datetime.timedelta(days=1)
            ).isoformat()
            loginTimestamp = request.session.get(
                f"is_kclogged_in_{str(evt.id)}_login", fallbackExpiration
            )
            
            if (
                not request.session.get("is_kclogged_in_" + str(evt.id), False)
                or (
                    datetime.datetime.fromisoformat(loginTimestamp) + datetime.timedelta(days=1)
                )
                < datetime.datetime.now()
            ):
                return registerEventLogin(request, event_url, evt)
            else:                
                response = view_func(request, event_url, evt, *args, **kwargs)
                return response

        return wrapper
    
    return decorator
