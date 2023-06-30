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
	subscriptions = models.ManyToManyField("PublicationList")
	criteria = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def collect(self):
		if self.criteria:
			try:
				query = create_advanced_query(self.criteria)
				collected = None
				for subscription in self.subscriptions.all():
					if collected:
						collected = collected | subscription.publications.filter(query)
					else:
						collected = subscription.publications.filter(query)
				return collected
			except BufferError:
				return None
		else:
			return self.publications

	def __str__(self):
		return f"{self.name} for {self.mapping}"


class UserPreferences(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	default_mapping = models.ForeignKey(Mapping, on_delete=models.SET_NULL, null=True)
	default_list = models.ForeignKey(PublicationList, on_delete=models.SET_NULL, null=True)
	default_page_size = models.PositiveSmallIntegerField(default=25)