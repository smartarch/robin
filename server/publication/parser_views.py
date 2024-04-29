import json
import re
from typing import Any

import requests
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from rest_framework import generics, mixins
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import serializers
from .models import Publication
from .parsers import DOIParser

from django.conf import settings

class ParseDOIView(mixins.ListModelMixin, generics.GenericAPIView):
	authentication_classes = [TokenAuthentication, BasicAuthentication]
	permission_classes = [IsAuthenticated]
	queryset = Publication.objects.all()
	serializer_class = serializers.PublicationSerializer

	@classmethod
	def get_publications_by_list_of_doi_list(cls, doi_list: [], extra_infos: dict = {}) -> []:
		publication_ids = []
		for doi in doi_list:
			# first, check if the DOI already exist in the database
			try:
				publication = Publication.objects.get(doi=doi)
			except ObjectDoesNotExist:
				doi_parser = DOIParser(doi)
				publication = doi_parser.parse(storage=settings.BASE_DIR / "storage/full_texts")

			if publication is not None:
				if doi in extra_infos:
					for key, value in extra_infos[doi].items(): # such as provided abstract
						if key in publication.__dict__ and len(publication.__dict__[key]) < len(value):
							publication.__dict__[key] = value
							publication.save()

				publication_ids.append(publication.id)
		return publication_ids

	def post(self, request, *args, **kwargs) -> Response:
		if 'doi' not in request.POST:
			raise BadRequest("Missing doi in POST data.")

		doi_list = request.POST.getlist("doi")
		publication_ids = ParseDOIView.get_publications_by_list_of_doi_list(doi_list)

		self.queryset = Publication.objects.filter(id__in=publication_ids)
		return self.list(request, *args, **kwargs)


class ParseBibView(mixins.ListModelMixin, generics.GenericAPIView):
	authentication_classes = [TokenAuthentication, BasicAuthentication]
	permission_classes = [IsAuthenticated]
	queryset = Publication.objects.all()
	serializer_class = serializers.PublicationSerializer

	def post(self, request, *args, **kwargs) -> Response:
		if 'bib_file' in request.FILES:
			try:
				bib_text = request.FILES.get('bib_file').file.read().decode('utf-8')
			except:
				bib_text = None
		else:
			bib_text = None if 'bib_text' not in request.POST else request.POST.get('bib_text')

		if bib_text is None:
			raise BadRequest("Missing bib_text or bib_file in POST data.")

		articles = bib_text.split('@')
		compiler = re.compile(r'(?P<key>\w+) = \{(?P<value>.+)\},')

		extra_infos = {}
		doi_list = []
		for article in articles:
			compiled_article = dict(compiler.findall(article))
			if "doi" in compiled_article:
				doi = compiled_article["doi"]
				doi_list.append(doi)
				if "abstract" in compiled_article:
					extra_infos[doi] = {"abstract": compiled_article['abstract']}

		publication_ids = ParseDOIView.get_publications_by_list_of_doi_list(doi_list, extra_infos)
		self.queryset = Publication.objects.filter(id__in=publication_ids)
		return self.list(request, *args, **kwargs)


class ParseLibView(mixins.ListModelMixin, generics.GenericAPIView):
	authentication_classes = [TokenAuthentication, BasicAuthentication]
	permission_classes = [IsAuthenticated]
	queryset = Publication.objects.all()
	serializer_class = serializers.PublicationSerializer

	libraries = ["IEEE", "SCOPUS"]

	@classmethod
	def get_library_ieee_as_response(cls, query, max_results=25) -> dict:
		params = {
			'params': {
				"querytext": query,
				"open_access": "False",
				"format": "json",
				"apikey": "dzw9ups3h3z7h78v4q5k37jz",
				"max_records": str(max_results),
			}
		}
		response = requests.get("http://ieeexploreapi.ieee.org/api/v1/search/articles", **params)
		if response.status_code == 200:
			return json.loads(response.text)

		return {'status_code': response.status_code}
	@classmethod
	def get_library_scopus_as_response(cls, query, max_results=10) -> dict:
		params = {
			"headers": {
				"Accept": "application/json",
				"X-ELS-APIKey": "8c18528a5bb1df340ec8e950e3342f95"
			},
			"params": {
				"start": 0,
				"count": str(max_results),
				"query": query
			}
		}
		response = requests.get("https://api.elsevier.com/content/search/scopus", **params)
		if response.status_code == 200:
			return json.loads(response.text)

		return {'status_code': response.status_code}


	@classmethod
	def orient_result_to_doi_form(cls, results, main_keyword) -> dict:
		doi_items = {}
		for item in results[main_keyword]:
			if "doi" in item:
				doi_items[item['doi']] = item

			elif "prism:doi" in item:
				doi_items[item['prism:doi']] = item

		return doi_items

	def get(self, request, *args, **kwargs) -> Response:
		if "library" not in kwargs:
			raise BadRequest("Library name missing from URL path.")

		if kwargs['library'].upper() not in ParseLibView.libraries:
			raise BadRequest(f"Library should be one of {', '.join(ParseLibView.libraries)}.")

		if "query" not in request.GET:
			raise BadRequest(f"Missing query in the data")

		if "max_results" in request.GET:
			max_results = request.GET.get("max_results")
		else:
			max_results = 25

		if kwargs['library'].upper() == "IEEE":
			results = ParseLibView.get_library_ieee_as_response(request.GET.get("query"), max_results)
			doi_based = ParseLibView.orient_result_to_doi_form(results, "articles")
			return Response(doi_based)

		elif kwargs['library'].upper() == "SCOPUS":
			results = ParseLibView.get_library_scopus_as_response(request.GET.get("query"), max_results)
			doi_based = ParseLibView.orient_result_to_doi_form(results["search-results"], "entry")
			return Response(doi_based)

		return Response({})
