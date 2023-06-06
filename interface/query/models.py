from django.db import models
from review.models import Review
from django.contrib.auth.models import User


class Query(models.Model):
	text = models.TextField()
	review = models.ForeignKey(Review, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)


class Platform(models.Model):
	name = models.CharField(max_length=128)


class QueryExecution(models.Model):
	platform = models.ForeignKey(Platform, on_delete=models.PROTECT)
	query = models.ForeignKey(Query, on_delete=models.CASCADE)
	results = models.TextField()
	executed_at = models.DateTimeField(auto_now_add=True)
