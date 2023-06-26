from django.db import models
from django.contrib.auth.models import User
from publication.models import Publication
from django.db.models import Q


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
	followers = models.ManyToManyField("PublicationList")
	criteria = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	# async def signal(self, publications : list[Publication]) -> None:
	# 	def parse_query (query: str) -> Q:
	# 		return Q()
	#
	# 	def parse_query(query, tokens):
	# 		if isinstance(tokens, list):
	# 			for operator in ('OR', 'AND'):
	# 				try:
	# 					index = tokens.index(operator)
	# 					break
	# 				except ValueError:
	# 					pass
	# 			else:
	# 				return q(query, tokens[0])
	# 			return (Q.__or__ if operator == 'OR' else Q.__and__)(
	# 				parse_query(query, tokens[:index]), q(query, tokens[index + 1:]))
	# 		else:
	# 			d = query[int(tokens)]
	# 			return Q(**{'__'.join((d['field'], d['operator'])): d['value']})




	def __str__(self):
		return f"{self.name} for {self.mapping}"


class UserPreferences(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	default_mapping = models.ForeignKey(Mapping, on_delete=models.SET_NULL, null=True)
	default_list = models.ForeignKey(PublicationList, on_delete=models.SET_NULL, null=True)
	default_page_size = models.PositiveSmallIntegerField(default=25)