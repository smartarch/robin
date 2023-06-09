from django.db import models
from django.contrib.auth.models import User
from publication.models import Publication


class Review(models.Model):
	name = models.CharField(max_length=128)
	description = models.TextField(blank=True)
	leader = models.ForeignKey(User, on_delete=models.PROTECT)
	reviewers = models.ManyToManyField(User, related_name="reviewer_users")
	secret_key = models.SlugField(max_length=255)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.name} by {self.leader.username}"


class PublicationList(models.Model):
	name = models.CharField(max_length=128)
	review = models.ForeignKey(Review, on_delete=models.CASCADE)
	publications = models.ManyToManyField(Publication)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.name} for {self.review}"


class UserPreferences(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	default_review = models.ForeignKey(Review, on_delete=models.SET_NULL, null=True)
	default_list = models.ForeignKey(PublicationList, on_delete=models.SET_NULL, null=True)
	default_page_size = models.PositiveSmallIntegerField(default=25)