import re
from django import template
from django.forms.utils import ErrorList

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
