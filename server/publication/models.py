from django.db import models
from .constants import VENUE_TYPES, FULL_TEXT_TYPES, FULL_TEXT_STATUS


class Source(models.Model):
	"""
		the source of the publication such as ACM, IEEE, ... etc.
	"""
	name = models.CharField(max_length=128)


class Country(models.Model):
	"""
		Country of origin (in time of publication) for authors' affiliations
	"""
	name = models.CharField(max_length=128, unique=True)


class Affiliation(models.Model):
	"""
		Affiliation of the authors
	"""
	institute = models.CharField(max_length=256)
	country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)


class Author(models.Model):
	"""
		Represents the author of the publications.
	"""
	first_name = models.CharField(max_length=256, blank=True)
	last_name = models.CharField(max_length=256)

	# optional fields
	affiliation = models.ForeignKey(Affiliation, on_delete=models.SET_NULL, null=True)
	ORCID = models.SlugField(max_length=1024, null=True)


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


class Keywords(models.Model):
	"""
		Represents the keywords assigned to publications
	"""
	keyword = models.CharField(max_length=256, unique=True)


class Publication(models.Model):
	"""
		The actual publication object
	"""
	doi = models.SlugField(max_length=256, unique=True)
	title = models.CharField(max_length=1024, unique=True)
	year = models.PositiveSmallIntegerField()
	datetime_added = models.DateTimeField(auto_now=True)

	venue = models.ForeignKey(Venue, on_delete=models.PROTECT)
	authors = models.ManyToManyField(Author)
	keywords = models.ManyToManyField(Keywords)

	# optional fields
	source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)
	abstract = models.TextField(blank=True)


class FullText(models.Model):
	"""
		Represents the full text files
	"""
	publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
	type = models.CharField(max_length=1, default="T", choices=FULL_TEXT_TYPES)
	status = models.CharField(max_length=1, default="E", choices=FULL_TEXT_STATUS)
	file = models.FileField(upload_to="full_text", blank=True)
