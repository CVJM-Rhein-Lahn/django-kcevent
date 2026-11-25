import sentry_sdk

FILTERED = "[Filtered]"

# Posted registration data contains personal data of (mostly underage)
# participants. Only the wizard management fields are kept, which are
# sufficient to debug the registration flow.
_ALLOWED_POST_FIELDS = ("wizard_goto_step",)
_ALLOWED_POST_SUFFIXES = ("-current_step",)
_PERSONAL_CONTEXT_PREFIXES = ("session.data", "kfh.", "forms.")


def _is_allowed_field(name) -> bool:
    return name in _ALLOWED_POST_FIELDS or str(name).endswith(_ALLOWED_POST_SUFFIXES)


def scrub_personal_data(event, hint):
    request = event.get("request")
    if isinstance(request, dict) and request.get("data"):
        data = request["data"]
        if isinstance(data, dict):
            request["data"] = {
                k: v if _is_allowed_field(k) else FILTERED for k, v in data.items()
            }
        else:
            request["data"] = FILTERED

    contexts = event.get("contexts")
    if isinstance(contexts, dict):
        for name in list(contexts):
            if name.startswith(_PERSONAL_CONTEXT_PREFIXES):
                contexts[name] = {"value": FILTERED}

    return event


def install_scrubber():
    """Chain scrub_personal_data in front of the configured before_send.

    before_send runs after all event processors (including the one adding the
    request body), so scrubbing there catches everything.
    """
    client = sentry_sdk.get_client()
    if not client.is_active():
        return

    previous = client.options.get("before_send")
    if getattr(previous, "_kcevent_scrubber", False):
        return

    def before_send(event, hint):
        event = scrub_personal_data(event, hint)
        if event is not None and previous is not None:
            return previous(event, hint)
        return event

    before_send._kcevent_scrubber = True
    client.options["before_send"] = before_send
