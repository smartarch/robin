from django.contrib import admin
from .models import Affiliation, Author, Country, Keyword, Publication, Venue, Source, FullText, FullTextAccess

admin.site.register(Affiliation)
admin.site.register(Author)
admin.site.register(Country)
admin.site.register(Keyword)
admin.site.register(Publication)
admin.site.register(Venue)
admin.site.register(Source)
admin.site.register(FullText)
admin.site.register(FullTextAccess)