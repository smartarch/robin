from typing import Any

from django.core.exceptions import BadRequest
from rest_framework import generics, mixins
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import serializers
from .models import Publication
from .parsers import DOIParser

class ParseDOIView(mixins.ListModelMixin, generics.GenericAPIView):
	authentication_classes = [TokenAuthentication, BasicAuthentication]
	permission_classes = [IsAuthenticated]
	queryset = Publication.objects.all()
	serializer_class = serializers.PublicationSerializer

	def post(self, request, *args, **kwargs) -> Response:
		if 'doi' not in request.POST:
			raise BadRequest("Missing doi in POST data.")

		doi_parser = DOIParser()
		doi_list = request.POST.getlist("doi")

		publication_ids = []
		for doi in doi_list:
			publication = doi_parser.parse(doi)
			publication_ids.append(publication.id)

		self.queryset.filter(id__in=publication_ids)
		return self.list(request, *args, **kwargs)


class ParseBibView(generics.GenericAPIView):
	pass
