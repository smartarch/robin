from django.contrib import admin
from .models import Affiliation, Author, Country, Keywords, Publication, Event, Source

admin.site.register(Affiliation)
admin.site.register(Author)
admin.site.register(Country)
admin.site.register(Keywords)
admin.site.register(Publication)
admin.site.register(Source)
admin.site.register(Event)
