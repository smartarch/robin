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


class UserField(models.Model):
	caption = models.CharField(max_length=64)
	value = models.CharField(max_length=2048)
	type = models.CharField(max_length=1, choices=[("T", "Text"), ("N", "Number"), ("B", "Boolean"), ("L", "List")])
	reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE)
	publication_list = models.ForeignKey(PublicationList, on_delete=models.CASCADE)
	@property
	def data(self) -> str | float | int | bool | list[str]:
		if self.type == "T":
			return self.value

		elif self.type == "N":
			if "." in self.value:
				return float(self.value)
			else:
				return int(self.value)

		elif self.type == "L":
			return self.value.split(",")

		else:
			return self.value.lower() == "true"

	@data.setter
	def data(self, value: str) -> None:
		self.value = value

	def __str__(self):
		return self.caption


class Review(models.Model):
	name = models.CharField(max_length=128)
	reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE)
	publication_list = models.ForeignKey(PublicationList, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.reviewer.short_name()

class Comment(models.Model):
	reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE)
	original = models.ForeignKey("Comment", on_delete=models.CASCADE, related_name="original_comment")
	review = models.ForeignKey(Review, on_delete=models.CASCADE)
	publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
	comment = models.TextField(blank=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

class UserFieldReview (models.Model):
	reviewer_field = models.ForeignKey(UserField, on_delete=models.CASCADE)
	publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
	review = models.ForeignKey(Review, on_delete=models.CASCADE)
	checked = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.reviewer_field.caption} - of {self.publication.title} as {self.checked}"

class UserPreferences(models.Model):
	user = models.ForeignKey(Reviewer, on_delete=models.CASCADE)
	default_mapping = models.ForeignKey(Mapping, on_delete=models.SET_NULL, null=True)
	default_list = models.ForeignKey(PublicationList, on_delete=models.SET_NULL, null=True)
	default_page_size = models.PositiveSmallIntegerField(default=25)


