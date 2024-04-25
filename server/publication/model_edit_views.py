from typing import Any

from django.db.models import QuerySet
from requests import Response
from rest_framework import mixins, generics
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer

from rest_framework.views import APIView

from .models import Source, Country, Affiliation, Author, Venue, Keyword, Publication, FullText
from . import serializers


class SerializedModelEditView(mixins.ListModelMixin,
								mixins.RetrieveModelMixin,
								mixins.UpdateModelMixin,
								mixins.DestroyModelMixin,
								mixins.CreateModelMixin,
								generics.GenericAPIView):
	authentication_classes = [TokenAuthentication, BasicAuthentication]
	permission_classes = [IsAuthenticated]
	queryset: QuerySet
	serializer_class: type(Serializer)

	def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
		if "pk" in kwargs:
			return self.retrieve(request, *args, **kwargs)
		return self.list(request, *args, **kwargs)

	def post(self, request, *args, **kwargs) -> Response:
		return self.create(request, *args, **kwargs)

	def put(self, request, *args, **kwargs) -> Response:
		return self.update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs) -> Response:
		return self.destroy(request, *args, **kwargs)


class SerializedSourceEditView(SerializedModelEditView):
	queryset = Source.objects.all()
	serializer_class = serializers.SourceSerializer


class SerializedCountryEditView(SerializedModelEditView):
	queryset = Country.objects.all()
	serializer_class = serializers.CountrySerializer


class SerializedAffiliationEditView(SerializedModelEditView):
	queryset = Affiliation.objects.all()
	serializer_class = serializers.AffiliationSerializer


class SerializedAuthorEditView(SerializedModelEditView):
	queryset = Author.objects.all()
	serializer_class = serializers.AuthorSerializer


class SerializedVenueEditView(SerializedModelEditView):
	queryset = Venue.objects.all()
	serializer_class = serializers.VenueSerializer


class SerializedKeywordEditView(SerializedModelEditView):
	queryset = Keyword.objects.all()
	serializer_class = serializers.KeywordSerializer


class SerializedPublicationEditView(SerializedModelEditView):
	queryset = Publication.objects.all()
	serializer_class = serializers.PublicationSerializer


class SerializedFullTextEditView(SerializedModelEditView):
	queryset = FullText.objects.all()
	serializer_class = serializers.FullTextSerializer
