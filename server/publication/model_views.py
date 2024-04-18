from typing import Any

from django.db.models import QuerySet
from django.utils.decorators import classonlymethod
from django.views.decorators.csrf import csrf_exempt
from requests import Response
from rest_framework import mixins, generics
from rest_framework.serializers import Serializer

from .models import Source, Country, Affiliation, Author, Venue, Keyword, Publication, FullText
from . import serializers


class SerializedModelView(mixins.ListModelMixin, mixins.RetrieveModelMixin, generics.GenericAPIView):
	queryset: QuerySet
	serializer_class: type(Serializer)

	def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
		if "pk" in kwargs:
			return self.retrieve(request, *args, **kwargs)
		return self.list(request, *args, **kwargs)



class SerializedSourceView(SerializedModelView):
	queryset = Source.objects.all()
	serializer_class = serializers.SourceSerializer


class SerializedCountryView(SerializedModelView):
	queryset = Country.objects.all()
	serializer_class = serializers.CountrySerializer


class SerializedAffiliationView(SerializedModelView):
	queryset = Affiliation.objects.all()
	serializer_class = serializers.AffiliationSerializer


class SerializedAuthorView(SerializedModelView):
	queryset = Author.objects.all()
	serializer_class = serializers.AuthorSerializer


class SerializedVenueView(SerializedModelView):
	queryset = Venue.objects.all()
	serializer_class = serializers.VenueSerializer


class SerializedKeywordView(SerializedModelView):
	queryset = Keyword.objects.all()
	serializer_class = serializers.KeywordSerializer


class SerializedPublicationView(SerializedModelView):
	queryset = Publication.objects.all()
	serializer_class = serializers.PublicationSerializer


class SerializedFullTextView(SerializedModelView):
	queryset = FullText.objects.all()
	serializer_class = serializers.FullTextSerializer
