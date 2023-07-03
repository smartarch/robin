from django.db import models
from django.contrib.auth.models import User
from publication.models import Publication
from .criteria import create_advanced_query

class Mapping(models.Model):
	name = models.CharField(max_length=128)
	description = models.TextField(blank=True)
	leader = models.ForeignKey(User, on_delete=models.PROTECT)
	reviewers = models.ManyToManyField(User, related_name="reviewer_users")
	secret_key = models.TextField(max_length=255)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.name} by {self.leader.username}"


class PublicationList(models.Model):
	name = models.CharField(max_length=128)
	mapping = models.ForeignKey(Mapping, on_delete=models.CASCADE)
	publications = models.ManyToManyField(Publication)
	followers = models.ManyToManyField("PublicationList", related_name="my_followers")
	subscriptions = models.ManyToManyField("PublicationList", related_name="my_subscriptions")
	criteria = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None ):
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


class UserPreferences(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	default_mapping = models.ForeignKey(Mapping, on_delete=models.SET_NULL, null=True)
	default_list = models.ForeignKey(PublicationList, on_delete=models.SET_NULL, null=True)
	default_page_size = models.PositiveSmallIntegerField(default=25)