from django.db import models
from .constants import FULL_TEXT_TYPES, FULL_TEXT_STATUS, VENUE_TYPES


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
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='affiliations')

    def __str__(self) -> str:
        return f"{self.institute} / {self.country.name}"


class Author(models.Model):
    """
        Represents the author of the publications.
    """
    first_name = models.CharField(max_length=1024)
    last_name = models.CharField(max_length=1024)

    # optional fields
    affiliation = models.ForeignKey(Affiliation, on_delete=models.CASCADE, blank=True, null=True, related_name="authors")
    ORCID = models.SlugField(max_length=1024, null=True)

    @property
    def name(self) -> str:
        return f"{self.last_name}, {self.first_name}"

    @property
    def short_name(self) -> str:
        return f"{str(self.first_name)[0]}. {self.last_name}"

    def __str__(self) -> str:
        return f"{self.last_name}"


class Venue(models.Model):
    """
        Represents the conference/journal of the publications.
    """
    name = models.CharField(max_length=2048)
    type = models.CharField(max_length=1, choices=VENUE_TYPES)

    # optional fields
    publisher = models.CharField(max_length=2048, blank=True)
    acronym = models.CharField(max_length=10, blank=True)
    volume = models.SlugField(blank=True)
    number = models.SlugField(blank=True)


    def __str__(self) -> str:
        return f"{self.get_type_display()} {self.name}"


class Keyword(models.Model):
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
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT)
    authors = models.ManyToManyField(Author)
    keywords = models.ManyToManyField(Keyword, related_name="publications")


    # optional links
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)

    abstract = models.TextField(blank=True)
    doi = models.SlugField(max_length=1024, unique=True)

    def __str__(self) -> str:
        return f"{self.title}, {self.id}"

    def all_authors(self):
        return self.authors.all().order_by('last_name')


class FullText(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="full_text")
    type = models.CharField(max_length=1, default="T", choices=FULL_TEXT_TYPES)
    url = models.URLField(max_length=1024, blank=True)

    def __str__(self):
        return f"{self.id} for {self.publication} is {self.get_type_display()} at {self.url}"


class FullTextAccess(models.Model):
    full_text = models.ForeignKey(FullText, on_delete=models.CASCADE, related_name="accesses")
    mapping = models.ForeignKey("mapping.Mapping", on_delete=models.CASCADE, related_name="full_text_accesses")
    file = models.FileField(upload_to="full_text", blank=True)
    status = models.CharField(max_length=1, default="E", choices=FULL_TEXT_STATUS)

    def delete(self, using=None, keep_parents=False):
        self.file.delete()
        super().delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        return f"{self.id} {self.full_text} for {self.mapping} is {self.get_status_display()}"