from django.contrib import admin
from .models import Source, Venue, Publication, Affiliation, Author, Keyword, FullText, Country
# Register your models here.

admin.site.register(Source)
admin.site.register(Country)
admin.site.register(Affiliation)
admin.site.register(Author)
admin.site.register(Keyword)
admin.site.register(Venue)
admin.site.register(Publication)
admin.site.register(FullText)


