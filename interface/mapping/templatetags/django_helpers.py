from django.template import Library

from mapping.models import ReviewField
from publication.models import Publication

register = Library()


@register.filter(name='lookup')
def lookup(dictionary: dict, key):
    return dictionary.get(key)


@register.simple_tag(name='get_field_value')
def get_field_value(field: ReviewField, publication: Publication):
    value = field.get_value_class().get_value(field, publication)
    if value:
        return value
    return ""
