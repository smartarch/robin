from django.db import models
from publication.models import Publication
from django.contrib.auth.models import User


class QueryPlatform (models.Model):
	key = models.CharField(max_length=2048)
	source = models.CharField(max_length=1024)
	params = models.TextField()
	url = models.URLField(null=True)
	help_link = models.URLField(null=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE)


class Query(models.Model):
	query = models.TextField()
	results = models.JSONField(null=True)
	found_publications = models.ManyToManyField(Publication)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	platform = models.ForeignKey(QueryPlatform, on_delete=models.SET_NULL ,null=True)
	created_at = models.DateTimeField(auto_now_add=True)
