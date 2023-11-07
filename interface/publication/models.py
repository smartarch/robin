from django.db import models

import os

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
    ORCID = models.SlugField(max_length=1024, null=True)

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
    name = models.CharField(max_length=2048)
    type = models.CharField(max_length=2048)

    # optional fields
    publisher = models.CharField(max_length=2048, blank=True)
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
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)

    abstract = models.TextField(blank=True)
    doi = models.SlugField(max_length=1024, unique=True)

    def __str__(self) -> str:
        return f"{self.title}"

    # def get_full_text(self):
    #     all_full_texts = FullText.objects.filter(publication=self)
    #     pdf_text = all_full_texts.filter(type="P")
    #     if pdf_text:
    #         if pdf_text[0].address:
    #             return f"/full_text/{pdf_text[0].address}"
    #         else:
    #             return pdf_text[0].url
    #     if all_full_texts:
    #         return all_full_texts[0].url
    #
    #     return None


class FullText(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    type = models.CharField(max_length=1, default="T",
            choices=[("H", "text/html"), ("P", "application/pdf"), ("X", "text/xml"), ("T", "text/plain")])

    url = models.URLField(max_length=1024, blank=True)


class FullTextAccess(models.Model):
    full_text = models.ForeignKey(FullText, on_delete=models.CASCADE)
    mapping = models.ForeignKey("mapping.Mapping", on_delete=models.CASCADE)
    file = models.FileField(upload_to="full_text", blank=True)
    status = models.CharField(max_length=1, default="E",
                              choices=[("E", "Empty"), ("N", "Not Found"), ("D", "Downloaded"), ("U", "Uploaded")])

    def delete(self, using=None, keep_parents=False):
        self.file.delete()
        super().delete(using=using, keep_parents=keep_parents)