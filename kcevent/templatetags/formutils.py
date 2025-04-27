from django import template
from django.forms.utils import ErrorList

register = template.Library()

@register.filter(name='combine_list')
def combine_list(value: ErrorList, arg):
    data: list = value.data
    if arg:
        data.extend(arg.data)
    new_list = ErrorList(data, value.error_class, value.renderer, value.field_id)
    return new_list