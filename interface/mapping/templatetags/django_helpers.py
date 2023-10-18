from django.template import Library


register = Library()


@register.filter(name='lookup')
def lookup(dictionary: dict, key):
    return dictionary.get(key)


@register.simple_tag(name='get_field_value')
def get_field_value(review_field_values, publication_id, field_id):
    field_value = review_field_values.get(publication_id, {}).get(field_id, "").first()
    if field_value:
        return field_value.value
    return ""
