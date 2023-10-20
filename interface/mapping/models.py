import json
from typing import Type, Optional

from django.db import models

# from local app
from .criteria import create_advanced_query

# from other apps
from publication.models import Publication
from reviewer.models import Reviewer


class Mapping(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    leader = models.ForeignKey(Reviewer, on_delete=models.PROTECT)
    reviewers = models.ManyToManyField(Reviewer, related_name="reviewer_users")
    secret_key = models.TextField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} by {self.leader.email}"


class PublicationList(models.Model):
    name = models.CharField(max_length=64)
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE)
    mapping = models.ForeignKey(Mapping, on_delete=models.CASCADE)
    publications = models.ManyToManyField(Publication, blank=True)
    type = models.CharField(max_length=1, choices=[("M", "Manual"), ("A", "Automated")], default="M")
    followers = models.ManyToManyField("PublicationList", related_name="my_followers", blank=True)
    subscriptions = models.ManyToManyField("PublicationList", related_name="my_subscriptions", blank=True)
    criteria = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.id:
            for follower in self.followers.all():
                query = create_advanced_query(follower.criteria)
                filtered_publications = self.publications.filter(query)
                if filtered_publications:
                    for pub in filtered_publications:
                        if pub not in follower.publications.all():
                            follower.publications.add(pub)
                            follower.save()

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f"{self.name} for {self.mapping}"


class ReviewField(models.Model):
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=1, choices=[("T", "Text"), ("N", "Number"), ("B", "Boolean"), ("L", "List"), ("S", "Select One"), ("O", "Multi-Select"), ("C", "Coding")])
    publication_list = models.ForeignKey(PublicationList, on_delete=models.CASCADE)

    def get_value_class(self) -> Type['ReviewFieldValue']:
        if self.type == "T":
            return ReviewFieldValueText
        elif self.type == "N":
            return ReviewFieldValueNumber
        elif self.type == "C":
            return ReviewFieldValueCoding
        raise NotImplementedError(f'ReviewField type {self.get_type_display()} is not yet implemented')

    def duplicate(self):
        old_pk = self.pk
        # duplicate this ReviewField (see https://docs.djangoproject.com/en/4.2/topics/db/queries/#copying-model-instances)
        self.pk = None
        self._state.adding = True
        self.save()

        # duplicate all `ReviewFieldValue`s of this ReviewField
        old_field = ReviewField.objects.get(pk=old_pk)
        value_object: ReviewFieldValue
        for value_object in self.get_value_class().objects.filter(review_field=old_field).all():
            value_object.pk = None
            value_object._state.adding = True
            value_object.review_field = self
            value_object.save()

    def __str__(self):
        return self.name


class ReviewFieldValue(models.Model):
    """Abstract class for all review field values. The concrete classes are defined below."""

    class Meta:
        abstract = True

    review_field = models.ForeignKey(ReviewField, on_delete=models.CASCADE)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    value = ...  # to be defined in the concrete subclass

    @staticmethod
    def save_value(field: ReviewField, publication: Publication, new_value):
        # find previous value object in the database
        value_object: Optional[ReviewFieldValue] = field.get_value_class().objects.filter(publication=publication).filter(review_field=field).first()

        if value_object:
            if new_value == "":  # new value is empty -> remove previous value object
                value_object.delete()
            else:  # update previous value object
                value_object.set_value(new_value)
                value_object.save()
        elif new_value != "":  # create new value object
            value_object = field.get_value_class()(review_field=field, publication=publication)
            value_object.set_value(new_value)
            value_object.save()

    @staticmethod
    def get_value(field: ReviewField, publication: Publication):
        value_object: Optional[ReviewFieldValue] = field.get_value_class().objects.filter(publication=publication).filter(review_field=field).first()
        if value_object:
            return value_object.value
        return None

    def set_value(self, new_value):
        raise NotImplementedError()  # to be implemented in the concrete subclass

    def __str__(self):
        return f'{self.review_field.name}: "{self.value}" for {self.publication.title}'


class ReviewFieldValueText(ReviewFieldValue):
    value = models.TextField()

    def set_value(self, new_value):
        self.value = new_value


class ReviewFieldValueNumber(ReviewFieldValue):
    value = models.FloatField()

    def set_value(self, new_value):
        self.value = float(new_value)


class ReviewFieldValueCoding(ReviewFieldValue):
    value = models.TextField()

    @staticmethod
    def save_value(field: ReviewField, publication: Publication, new_value):
        if new_value == "":
            new_codes = set()
        else:
            new_codes = set(tag["value"] for tag in json.loads(new_value))
        current_code_objects: dict[str, ReviewFieldValueCoding] = {
            code_object.value: code_object
            for code_object in ReviewFieldValueCoding.objects.filter(publication=publication).filter(review_field=field).all()
        }
        current_codes = set(current_code_objects.keys())

        removed_codes = current_codes - new_codes
        added_codes = new_codes - current_codes

        for code in removed_codes:
            current_code_objects[code].delete()
        for code in added_codes:
            new_code_object = ReviewFieldValueCoding(review_field=field, publication=publication, value=code)
            new_code_object.save()

    @staticmethod
    def get_value(field: ReviewField, publication: Publication):
        code_objects = ReviewFieldValueCoding.objects.filter(publication=publication).filter(review_field=field).all()
        return json.dumps([{"value": code_object.value} for code_object in code_objects])

    @staticmethod
    def get_all_codes(field: ReviewField):
        code_objects = ReviewFieldValueCoding.objects.filter(review_field=field).all()
        codes = set(code_object.value for code_object in code_objects)
        return codes

    @staticmethod
    def rename_code(field: ReviewField, old_code: str, new_code: str):
        code_objects = ReviewFieldValueCoding.objects.filter(review_field=field).filter(value=old_code).all()
        for code_object in code_objects:
            code_object.value = new_code
            code_object.save()


class Comment(models.Model):
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE)
    original = models.ForeignKey("Comment", on_delete=models.CASCADE, related_name="original_comment")
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    comment = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserPreferences(models.Model):
    user = models.ForeignKey(Reviewer, on_delete=models.CASCADE)
    default_mapping = models.ForeignKey(Mapping, on_delete=models.SET_NULL, null=True)
    default_list = models.ForeignKey(PublicationList, on_delete=models.SET_NULL, null=True)
    default_page_size = models.PositiveSmallIntegerField(default=25)
