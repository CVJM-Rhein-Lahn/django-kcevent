import re
from django import template
from django.forms.utils import ErrorList
from django.forms import BoundField

register = template.Library()
numeric_test = re.compile("^\d+$")


@register.filter(name="combine_list")
def combine_list(value: ErrorList, arg):
    data: list = value.data
    if arg:
        data.extend(arg.data)
    new_list = ErrorList(data, value.error_class, value.renderer, value.field_id)
    return new_list


@register.filter(name="attr")
def attr(value, arg):
    """Gets an attribute of an object dynamically from a string name"""

    try:
        element = value.__getitem__(arg)
        return element
    except AttributeError:
        pass
    
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, "has_key") and value.has_key(arg):
        return value[arg]
    elif (
        isinstance(value, list)
        and numeric_test.match(str(arg))
        and len(value) > int(arg)
    ):
        return value[int(arg)]
    else:
        return ""


@register.filter(name="field_display_value")
def field_display_value(bound_field: BoundField):
    """Return the human-readable display value of a BoundField without rendering its widget."""
    field = bound_field.field
    value = bound_field.value()
    if value is None or value == "":
        return ""
    # Choice fields: look up the label for the current value
    if hasattr(field, "choices"):
        for choice_val, choice_label in field.choices:
            if str(choice_val) == str(value):
                return choice_label
    return value
