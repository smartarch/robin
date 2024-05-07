from django.template import Library
from django.utils.html import mark_safe, conditional_escape

from mapping.models import (ReviewField, ReviewFieldValueCoding, Mapping, ReviewFieldValue, ReviewFieldValueText,
                            ReviewFieldValueBoolean, ReviewFieldValueNumber)
from publication.models import Publication
from reviewer.models import Reviewer

register = Library()


@register.filter(name='lookup')
def lookup(dictionary: dict, key):
    return dictionary.get(key)


@register.simple_tag(name='get_field_value')
def get_field_value(field: ReviewField, publication: Publication, reviewer: Reviewer):
    value = field.get_value_class().get_value(field, publication, reviewer)
    if value:
        return value
    return ""


@register.simple_tag(name='get_others_values')
def get_others_values(field: ReviewField, publication: Publication, reviewer: Reviewer):
    values = field.get_value_class().get_others_values(field, publication, reviewer)
    return values


@register.simple_tag(name='who_reviewed_publication')
def who_reviewed_publication(mapping: Mapping, pub: Publication):
    reviewers = [review_field_value.reviewer for review_field_value in
            ReviewFieldValueCoding.objects.filter(review_field__mapping=mapping).filter(publication=pub).union(
                ReviewFieldValueText.objects.filter(review_field__mapping=mapping).filter(publication=pub).union(
                    ReviewFieldValueBoolean.objects.filter(review_field__mapping=mapping).filter(publication=pub).union(
                        ReviewFieldValueNumber.objects.filter(review_field__mapping=mapping).filter(publication=pub))))
    ]
    return set(reviewers)


@register.simple_tag(name='coding_codes_list')
def coding_codes_list(field: ReviewField):
    # escape the characters inside each code and wrap codes in quotation marks
    # the HTML/JS comments prevent "</script>" inside the code from being interpreted (https://stackoverflow.com/a/28643409)

    def escape(code):
        return code.replace('"', '\\"')  # escape only quotation marks
        # return conditional_escape(code)  # escapes all special characters

    return mark_safe("/*<!--*/ [" + ", ".join(f'"{escape(code)}"' for code in ReviewFieldValueCoding.get_all_codes(field)) + "] /*-->*/")
