from typing import List

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Model
from requests import Response
from rest_framework.serializers import Serializer
import xml.etree.ElementTree as ET
from .models import Source, Country, Affiliation, Author, Venue, Keyword, Publication, FullText
from .serializers import AuthorSerializer, AffiliationSerializer, CountrySerializer, VenueSerializer, \
	PublicationSerializer, SourceSerializer


class GenericModelFactory:
	model: type(models.Model)
	serializer_class: type(Serializer)

	def __init__(self, _model, _serializer_class) -> None:
		self.model = _model
		self.serializer_class = _serializer_class

	def find_object(self, data: dict) -> models.Model | None:
		try:
			if self.model == Source or self.model == Country or self.model == Venue:
				return self.model.objects.get(name=data['name'])

			if self.model == Affiliation:
				return self.model.objects.get(institute=data['institute'])

			if self.model == Author:
				return self.model.objects.filter(last_name=data['last_name']).get(first_name=data['first_name'])

			if self.model == Keyword:
				return self.model.objects.get(keyword=data['keyword'])

			if self.model == Publication:
				return self.model.objects.get(doi=data['doi'])

		except ObjectDoesNotExist:
			print (f"object was not found for {self.model} and {data}")
			return None

	def create_or_get(self, data: dict) -> models.Model| None:
		instance = self.find_object(data)
		if instance is None:
			return self.model(**data)

		return instance


class DOIParser:
	req: Response
	doi: str
	venue_types = {
		"conference_paper": "conference",
		"journal_article": "journal",
	}

	def __init__(self, doi: str):
		url = f"https://dx.doi.org/{doi}"
		self.req = requests.get(url, headers={"Accept": "application/vnd.crossref.unixsd+xml"})
		self.ns = {
			'qr': 'http://www.crossref.org/qrschema/3.0',
			'x': 'http://www.crossref.org/xschema/1.1'
		}
		self.doi = doi

	def xml_find_items(self, root, namespace, query, singleton=True):
		items = root.findall(f".//{namespace}:{query}", self.ns)
		if not items:
			return None

		if singleton and len(items) != 1:
			return None

		if singleton:
			return items[0]
		else:
			return items

	def parse(self) -> None | Publication:
		if self.req.status_code != 200:
			print("doi not found")
			return None

		xml_data = self.req.text
		root = ET.fromstring(xml_data)

		query = self.xml_find_items(root=root, namespace="qr", query="query")
		if query is None:
			print("error in finding query")
			return None

		if 'status' not in query.attrib or query.attrib['status'] != 'resolved':
			print("error in status")
			return None

		publisher_name = self.xml_find_items(root=query, namespace="x", query="publisher_name")
		doi_type = self.xml_find_items(root=query, namespace="qr", query="doi")

		if doi_type is None:
			print("error in finding doi type")
			return None

		if publisher_name is not None:
			publisher_name = publisher_name.text
		else:
			publisher_name = ""

		# e.g conference paper
		doi_type = doi_type.attrib["type"]

		record = self.xml_find_items(root=query, namespace="qr", query="doi_record")
		if record is None:
			print("error in finding record")
			return None

		venue = self.xml_find_items(root=record, namespace="x", query=DOIParser.venue_types[doi_type])
		if venue is None:
			print("error in finding venue")
			return None

		publication = self.xml_find_items(root=venue, namespace="x", query=doi_type)
		if publication is None:
			print("error in finding publication")
			return None

		contributors = self.xml_find_items(root=publication, namespace="x", query="contributors")

		if contributors is None:
			print("error in finding contributors")
			return None

		authors = self.resolve_authors(contributors)
		venue_object = self.resolve_venue(venue, DOIParser.venue_types[doi_type], publisher_name)
		dates = self.xml_find_items(root=publication, namespace="x", query="publication_date", singleton=False)

		if dates is None:
			print("error in finding publication dates")
			return None

		year = None
		for publication_date in dates:
			year = self.xml_find_items(root=publication_date, namespace="x", query="year")
			if year is not None:
				year = year.text
				break

		if year is None:
			print("error in finding year")
			return None

		title = self.xml_find_items(root=publication, namespace="x", query="title")
		if title is None:
			print("error in finding title")
			return None

		# finally creating the publication
		source_factory = GenericModelFactory(Source, SourceSerializer)
		source = source_factory.create_or_get(data={"name": "crossref"})
		source.save()

		publication_factory = GenericModelFactory(Publication, PublicationSerializer)
		publication = publication_factory.create_or_get(data={
			"doi": self.doi,
			"title": title.text,
			"year": year,
			"venue": venue_object,
			"source": source})

		if publication is None or not isinstance(publication, Publication):
			print("failed at creating the publication")
			return None

		publication.save()
		for author in authors:
			publication.authors.add(author)

		publication.save()
		return publication

	def resolve_venue(self, venue, venue_type, publisher_name) -> Venue | None:

		if venue_type == "conference":
			synonyms_for_conference_names = ["conference_name", "proceedings_title"]
			conference_name = None

			for synonym in synonyms_for_conference_names:
				conference_name = self.xml_find_items(root=venue, namespace="x", query=synonym)
				if conference_name is not None:
					break

			if conference_name is not None:
				conference_factory = GenericModelFactory(Venue, VenueSerializer)
				conference = conference_factory.create_or_get(data={"name": conference_name.text})
				if conference is not None:
					# ("P", "Conference Proceedings"),
					conference.type = "P"
					conference.publisher = publisher_name
					conference.save()

				return conference

		if venue_type == "journal":
			synonyms_for_journal_names = ["full_title", "journal_title"]
			journal_name = None

			for synonym in synonyms_for_journal_names:
				journal_name = self.xml_find_items(root=venue, namespace="x", query=synonym)
				if journal_name is not None:
					break

			if journal_name is not None:
				journal_factory = GenericModelFactory(Venue, VenueSerializer)
				journal = journal_factory.create_or_get(data={"name": journal_name.text})
				if journal is not None:
					# ("J", "Journal Article"),
					journal.type = "P"

					issue = self.xml_find_items(root=venue, namespace="x", query="issue")
					if issue is not None:
						journal.issue = issue

					volume = self.xml_find_items(root=venue, namespace="x", query="volume")
					if volume is not None:
						journal.volume = volume

					journal.publisher = publisher_name
					journal.save()

				return journal
		return None

	def resolve_affiliation(self, affiliation_element) -> Model | None:
		if affiliation_element is not None:
			parsed_affiliation = affiliation_element.text.split(',')
			if len(parsed_affiliation) > 1:
				country_name = parsed_affiliation[-1]
				institute = ",".join(parsed_affiliation[0:-1])
			else:
				country_name = "EMPTY"
				institute = parsed_affiliation[0]

			country_factory = GenericModelFactory(Country, CountrySerializer)
			country = country_factory.create_or_get(data={"name": country_name.strip()})
			if country is not None:
				country.save()

			affiliation_factory = GenericModelFactory(Affiliation, AffiliationSerializer)
			affiliation = affiliation_factory.create_or_get(data={
				"institute": institute.strip()})

			if affiliation is not None:
				affiliation.country = country
				affiliation.save()

			return affiliation

		return None

	def resolve_authors(self, contributors) -> List[Model]:
		synonyms_for_first_names = ["first_name", "firstname", "given_name", "givenname"]
		synonyms_for_last_names = ["last_name", "lastname", "surname", "family_name", "familyname"]

		authors = []

		for contributor in contributors:
			last_name = None
			first_name = None

			for synonym in synonyms_for_last_names:
				last_name = self.xml_find_items(root=contributor, namespace="x", query=synonym)
				if last_name is not None:
					break

			for synonym in synonyms_for_first_names:
				first_name = self.xml_find_items(root=contributor, namespace="x", query=synonym)
				if first_name is not None:
					break

			affiliation = self.xml_find_items(root=contributor, namespace="x", query="affiliation")

			if last_name is not None and first_name is not None:
				author_factory = GenericModelFactory(_model=Author, _serializer_class=AuthorSerializer)
				created_affiliation = None
				if affiliation is not None:
					created_affiliation = self.resolve_affiliation(affiliation)

				author = author_factory.create_or_get(data={
					"last_name": last_name.text,
					"first_name": first_name.text,
					"affiliation": created_affiliation
				})
				author.save()
				authors.append(author)

		return authors


	def resolve_full_text(self, query):
		pass

	def resolve_keywords(self, query):
		pass