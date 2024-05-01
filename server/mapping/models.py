import json
from typing import Type, Optional
from django.db import models
from .constants import REVIEW_FIELD_TYPES, PUBLICATION_LIST_TYPES


class Mapping(models.Model):
    # required
    name = models.CharField(max_length=128)

    # relations
    # protect the mapping not to be deleted if the user is deleted
    leader = models.ForeignKey("reviewer.Reviewer", on_delete=models.PROTECT, related_name="mapping_leader")
    reviewers = models.ManyToManyField("reviewer.Reviewer", related_name="mapping_reviewers")

    # optionals
    description = models.TextField(blank=True)

    # auto
    secret_key = models.TextField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} by {self.leader.email}"


class PublicationList(models.Model):
    # required
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=1, choices=PUBLICATION_LIST_TYPES, default="M")

    # relations
    reviewer = models.ForeignKey("reviewer.Reviewer", on_delete=models.CASCADE, related_name="pl_owner")
    mapping = models.ForeignKey(Mapping, on_delete=models.CASCADE, related_name="pl_mapping")

    publications = models.ManyToManyField("publication.Publication", blank=True, related_name="pl_publications")
    followers = models.ManyToManyField("PublicationList", related_name="pl_followers", blank=True)
    subscriptions = models.ManyToManyField("PublicationList", related_name="pl_subscriptions", blank=True)

    # optional
    criteria = models.TextField(blank=True)

    # auto
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
            in case of subscribed lists, update them automatically if their list is updated
        """
        if self.id:
            # from local app
            from .criteria import create_advanced_query

            for follower in self.followers.all():
                # create a query for the followers
                query = create_advanced_query(self.mapping, self, follower.criteria)

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
    type = models.CharField(max_length=1, choices=REVIEW_FIELD_TYPES, default="T")
    mapping = models.ForeignKey(Mapping, on_delete=models.CASCADE)

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
    publication = models.ForeignKey("publication.Publication", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    value = ...  # to be defined in the concrete subclass

    @staticmethod
    def save_value(field: ReviewField, publication, new_value):
        # find previous value object in the database
        value_object: Optional[ReviewFieldValue] = \
            field.get_value_class().objects.filter(publication=publication).filter(review_field=field).first()

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
    def get_value(field: ReviewField, publication):
        value_object: Optional[ReviewFieldValue]  \
            = field.get_value_class().objects.filter(publication=publication).filter(review_field=field).first()
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
    def save_value(field: ReviewField, publication, new_value):
        if new_value == "":
            new_codes = set()
        else:
            new_codes = set(tag["value"] for tag in json.loads(new_value))
        current_code_objects: dict[str, ReviewFieldValueCoding] = {
            code_object.value: code_object
            for code_object in \
                ReviewFieldValueCoding.objects.filter(publication=publication).filter(review_field=field).all()
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
    def get_value(field: ReviewField, publication):
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
    # relations
    reviewer = models.ForeignKey("reviewer.Reviewer", on_delete=models.CASCADE)
    original = models.ForeignKey("Comment", on_delete=models.CASCADE, related_name="original_comment")
    publication = models.ForeignKey("publication.Publication", on_delete=models.CASCADE)

    # optional
    comment = models.TextField(blank=False)

    # auto
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserPreferences(models.Model):
    # relations
    user = models.ForeignKey("reviewer.Reviewer", on_delete=models.CASCADE)
    default_mapping = models.ForeignKey(Mapping, on_delete=models.SET_NULL, null=True)
    default_list = models.ForeignKey(PublicationList, on_delete=models.SET_NULL, null=True)

    # optional
    default_page_size = models.PositiveSmallIntegerField(default=25)
