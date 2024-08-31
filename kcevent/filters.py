from django.contrib import admin
from django.utils.translation import gettext_lazy as _
import datetime
from django.db.models import F

def custom_list_title_filter(title):
    class Wrapper(admin.AllValuesFieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.AllValuesFieldListFilter(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper

class is_event_future(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Is event in future?")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "is_event_future"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ("yes", _("In future")),
            ("no", _("In past")),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == "yes":
            return queryset.filter(
                end_date__gte=datetime.datetime.now(),
            )
        elif self.value() == "no":
            return queryset.filter(
                end_date__lt=datetime.datetime.now(),
            )
        else:
            return queryset

class is_27_and_older(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("Is >= 27")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "is_27"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ("yes", _("Is >= 27")),
            ("no", _("Is < 27")),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == "yes":
            return queryset.filter(
                reg_user__birthday__lte=F("reg_event__start_date") - datetime.datetime.timedelta(weeks=52*27),
            )
        elif self.value() == "no":
            return queryset.filter(
                reg_user__birthday__gt=F("reg_event__start_date") - datetime.datetime.timedelta(weeks=52*27),
            )
        else:
            return queryset
