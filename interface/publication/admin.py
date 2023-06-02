from django.contrib import admin
from .models import Affiliation, Author, Country, Keywords, Publication, Event, Source

@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = ("institute","country")
    search_fields = ("institute","country")
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "affiliation")
    search_fields = ("first_name", "last_name", "affiliation")

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "other_forms")
    search_fields = ("name", "other_forms")


@admin.register(Keywords)
class KeywordsAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ("doi", "title")
    search_fields = ("doi", "title", "abstract", "keywords", "author")

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "publisher", "type")
    search_fields = ("name", "publisher", "type")
