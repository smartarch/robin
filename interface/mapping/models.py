from typing import Type

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
            return ReviewFieldValueText  # TODO
        raise NotImplementedError(f'ReviewField type {self.get_type_display()} is not yet implemented')

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
