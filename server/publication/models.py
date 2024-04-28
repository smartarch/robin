from django.db import models
from .constants import VENUE_TYPES, FULL_TEXT_TYPES, FULL_TEXT_STATUS


class Source(models.Model):
	"""
		the source of the publication such as ACM, IEEE, ... etc.
	"""
	name = models.CharField(max_length=128)

	def __str__(self):
		return f"{self.name}"


class Country(models.Model):
	"""
		Country of origin (in time of publication) for authors' affiliations
	"""
	name = models.CharField(max_length=128, unique=True)

	def __str__(self):
		return f"{self.name}"


class Affiliation(models.Model):
	"""
		Affiliation of the authors
	"""
	institute = models.CharField(max_length=256)
	country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, related_name='institutes')

	def __str__(self):
		return f"{self.institute}, {self.country.name if self.country else 'NONE' }"


class Author(models.Model):
	"""
		Represents the author of the publications.
	"""
	first_name = models.CharField(max_length=256, blank=True)
	last_name = models.CharField(max_length=256)

	# optional fields
	affiliation = models.ForeignKey(Affiliation, on_delete=models.SET_NULL, null=True, related_name="authors")
	ORCID = models.SlugField(max_length=1024, null=True)

	def __str__(self):
		return f"{self.first_name} {self.last_name}, {self.affiliation }"


class Venue(models.Model):
	"""
		Represents the venue of the publication
	"""
	name = models.CharField(max_length=256)
	type = models.CharField(max_length=1, choices=VENUE_TYPES)

	# optional fields
	publisher = models.CharField(max_length=256, blank=True)
	volume = models.CharField(max_length=128)
	issue = models.CharField(max_length=128)

	def __str__(self):
		return f"{self.name} {self.type}, {self.publisher }"

class Keyword(models.Model):
	"""
		Represents the keywords assigned to publications
	"""
	keyword = models.CharField(max_length=256, unique=True)

	def __str__(self):
		return f"{self.keyword}"


class Publication(models.Model):
	"""
		The actual publication object
	"""
	doi = models.SlugField(max_length=256, unique=True)
	title = models.CharField(max_length=1024, unique=True)
	year = models.PositiveSmallIntegerField()
	datetime_added = models.DateTimeField(auto_now=True)

	venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="papers")
	authors = models.ManyToManyField(Author, related_name="published_papers")
	keywords = models.ManyToManyField(Keyword, related_name="related_papers")

	# optional fields
	source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, related_name="publications")
	abstract = models.TextField(blank=True)
	first_created = models.DateTimeField(auto_now_add=True)
	last_update = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.title}, {self.year}"


class FullText(models.Model):
	"""
		Represents the full text files
	"""
	publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="full_texts")
	type = models.CharField(max_length=1, default="T", choices=FULL_TEXT_TYPES)
	status = models.CharField(max_length=1, default="E", choices=FULL_TEXT_STATUS)
	file = models.FileField(upload_to="full_text", blank=True)
	first_created = models.DateTimeField(auto_now_add=True)
	last_update = models.DateTimeField(auto_now=True)