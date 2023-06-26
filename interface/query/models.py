from django.db import models
from mapping.models import PublicationList
from django.contrib.auth.models import User


class Query(models.Model):
	text = models.TextField()
	publication_list = models.ForeignKey(PublicationList, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

