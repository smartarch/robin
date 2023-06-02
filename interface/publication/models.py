from django.db import models
from django.contrib.auth.models import User
import re


class Source(models.Model):
    """
        Represents the source of publication (i.e. ACM, IEEE, SCOPUS ...).
    """
    name = models.CharField(max_length=1024)

    def __str__(self) -> str:
        return f"{self.name}"


class Country(models.Model):
    """
        Represents the country of authors of the publications.
    """
    name = models.CharField(max_length=1024, unique=True)
    other_forms = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.name}"


class Affiliation(models.Model):
    """
        Represents the affiliation of authors of the publications.
    """
    institute = models.CharField(max_length=1024)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.institute} / {self.country.name}"


class Author(models.Model):
    """
        Represents the author of the publications.
    """
    first_name = models.CharField(max_length=1024)
    last_name = models.CharField(max_length=1024)

    # optional fields
    affiliation = models.ForeignKey(Affiliation, on_delete=models.CASCADE, blank=True, null=True)
    identifier = models.SlugField(max_length=1024, blank=True)

    @property
    def name(self) -> str:
        return f"{self.last_name}, {self.first_name}"

    @property
    def short_name(self) -> str:
        return f"{str(self.first_name)[0]}. {self.last_name}"

    def __str__(self) -> str:
        return f"{self.last_name}"


class Event(models.Model):
    """
        Represents the conference/journal of the publications.
    """
    name = models.CharField(max_length=2014)
    type = models.CharField(max_length=2014)

    # optional fields
    publisher = models.CharField(max_length=2014, blank=True)
    acronym = models.CharField(max_length=10, blank=True)
    volume = models.SlugField(blank=True)
    number = models.SlugField(blank=True)

    def __str__(self) -> str:
        return f"{self.name}"


class Keywords(models.Model):
    """
        Represents the keywords of the publications.
    """
    name = models.CharField(max_length=512, unique=True)

    def __str__(self) -> str:
        return f"{self.name}"


class Publication(models.Model):
    """
        Represents the publication.
    """
    title = models.CharField(max_length=1024)
    clean_title = models.CharField(max_length=1024)                     # no space and no symbols, all lower case
    year = models.PositiveSmallIntegerField()
    date_added = models.DateField(auto_now=True)

    # A venue is prevented to be deleted if there are publications in it
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    authors = models.ManyToManyField(Author)
    author_keywords = models.ManyToManyField(Keywords, related_name="author_keys")
    index_keywords = models.ManyToManyField(Keywords, related_name="index_keys")

    # optional links
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)

    # optional fields
    citations = models.PositiveIntegerField(default=0)
    abstract = models.TextField(blank=True)
    doi = models.SlugField(max_length=1024, blank=True)
    url = models.URLField(max_length=1024, blank=True)
    note = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.title}"

    # def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
    #     self.clean_title = re.sub('[^a-zA-Z0-9]+', '', str(self.title)).lower()
    #     super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
