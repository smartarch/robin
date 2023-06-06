from django.db import models
from django.contrib.auth.models import User
from publication.models import Publication


class PublicationList(models.Model):
	name = models.CharField(max_length=128)
	publications = models.ManyToManyField(Publication)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)


class Review(models.Model):
	leader = models.ForeignKey(User, on_delete=models.PROTECT)
	reviewers = models.ManyToManyField(User, related_name="reviewer_users")
	publication_lists = models.ManyToManyField(PublicationList)
	secret_key = models.SlugField(max_length=50)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)


class Journal(models.Model):
	review = models.ForeignKey(Review, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	message = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
