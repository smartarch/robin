import os
from pathlib import Path
from typing import List

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Model
from pypdf import PdfReader
from requests import Response
import xml.etree.ElementTree as ET

from .constants import FULL_TEXT_TYPES_REVERSE
from .models import Source, Country, Affiliation, Author, Venue, Keyword, Publication, FullText

class GenericModelFactory:
	model: type(models.Model)

	def __init__(self, _model) -> None:
		self.model = _model

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

			if self.model == FullText:
				return self.model.objects.get(url=data['url'])

		except ObjectDoesNotExist:
			print (f"object was not found for {self.model}")
			return None

	def create_or_get(self, data: dict) -> models.Model| None:
		instance = self.find_object(data)
		if instance is None:
			return self.model(**data)

		return instance

class Parser:
	def parse(self, storage: Path) -> None | Publication:
		raise NotImplementedError


class DOIParser(Parser):
	xml_resp: Response
	json_resp: Response
	doi: str
	venue_types = {
		"conference_paper": "conference",
		"journal_article": "journal",
	}

	def __init__(self, doi: str):
		url = f"https://dx.doi.org/{doi}"
		try:
			self.xml_resp = requests.get(url, headers={"Accept": "application/vnd.crossref.unixsd+xml"})
		except:
			print ("The server is down or not accepting xml")

		try:
			self.json_resp = requests.get(url, headers={"Accept": "application/json"})
		except:
			print("The server is down or not accepting json")

		self.xml_ns = {
			'qr': 'http://www.crossref.org/qrschema/3.0',
			'x': 'http://www.crossref.org/xschema/1.1',
			'any': '*',
		}
		self.doi = doi

	def xml_find_items(self, root, namespace, query, singleton=True):
		items = root.findall(f".//{namespace}:{query}", self.xml_ns)
		if not items:
			return None

		if singleton and len(items) != 1:
			return None

		if singleton:
			return items[0]
		else:
			return items

	def parse_xml(self, storage: Path) -> None | Publication:
		if self.xml_resp.status_code != 200:
			print("doi not found")
			return None

		xml_data = self.xml_resp.text

		try:
			root = ET.fromstring(xml_data)
		except ET.ParseError as e:
			print(f"error reading from xml: {e}")
			return None

		query = self.xml_find_items(root=root, namespace="any", query="query")
		if query is None:
			print("error in finding query")
			return None

		if 'status' not in query.attrib or query.attrib['status'] != 'resolved':
			print("error in status")
			return None

		publisher_name = self.xml_find_items(root=query, namespace="any", query="publisher_name")
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

		record = self.xml_find_items(root=query, namespace="any", query="doi_record")
		if record is None:
			print("error in finding record")
			return None

		venue = self.xml_find_items(root=record, namespace="any", query=DOIParser.venue_types[doi_type])

		if venue is None:
			print("error in finding venue")
			return None

		venue_object = self.resolve_venue(venue, DOIParser.venue_types[doi_type], publisher_name)

		publication = self.xml_find_items(root=venue, namespace="any", query=doi_type)
		if publication is None:
			print("error in finding publication")
			return None

		contributors = self.xml_find_items(root=publication, namespace="any", query="contributors")

		if contributors is None:
			print("error in finding contributors")
			return None

		authors = self.resolve_authors(contributors)
		dates = self.xml_find_items(root=publication, namespace="qr", query="publication_date", singleton=False)

		if dates is None:
			dates = self.xml_find_items(root=record, namespace="any", query="publication_date", singleton=False)
			if dates is None:
				print("error in finding publication dates")
				return None

		year = None
		for publication_date in dates:
			year = self.xml_find_items(root=publication_date, namespace="any", query="year")
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

		# optional stuff
		abstract = ""
		abstract_element = self.xml_find_items(root=publication, namespace="any", query="abstract")
		if abstract_element is not None:
			abstract_p = self.xml_find_items(root=abstract_element, namespace="any", query="p")
			if abstract_p is not None:
				abstract = abstract_p.text

		# finally creating the publication
		source_factory = GenericModelFactory(Source)
		source = source_factory.create_or_get(data={"name": "CrossRef"})
		source.save()

		publication_factory = GenericModelFactory(Publication)
		publication_object = publication_factory.create_or_get(data={
			"doi": self.doi,
			"title": title.text,
			"year": year,
			"venue": venue_object,
			"source": source,
			"abstract": abstract,
		})

		if publication_object is None or not isinstance(publication_object, Publication):
			print("failed at creating the publication")
			return None

		publication_object.save()
		for author in authors:
			publication_object.authors.add(author)

		publication_object.save()

		# models which have publication as foreign key
		full_texts = self.resolve_full_text(storage, publication)
		for filename , full_text in full_texts:
			full_text_factory = GenericModelFactory(FullText)
			full_text_object = full_text_factory.create_or_get(full_text)
			if full_text_object is not None and isinstance(full_text_object, FullText):
				full_text_object.publication = publication_object
				full_text_object.file.name = str(filename)
				full_text_object.save()

		return publication_object

	def resolve_venue(self, venue, venue_type, publisher_name) -> Venue | None:

		if venue_type == "conference":
			synonyms_for_conference_names = ["conference_name", "proceedings_title"]
			conference_name = None

			for synonym in synonyms_for_conference_names:
				conference_name = self.xml_find_items(root=venue, namespace="any", query=synonym)
				if conference_name is not None:
					break

			if conference_name is not None:
				conference_factory = GenericModelFactory(Venue)
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
				journal_name = self.xml_find_items(root=venue, namespace="any", query=synonym)
				if journal_name is not None:
					break

			if journal_name is not None:
				journal_factory = GenericModelFactory(Venue)
				journal = journal_factory.create_or_get(data={"name": journal_name.text})
				if journal is not None:
					# ("J", "Journal Article"),
					journal.type = "P"

					issue = self.xml_find_items(root=venue, namespace="any", query="issue")
					if issue is not None:
						journal.issue = issue

					volume = self.xml_find_items(root=venue, namespace="any", query="volume")
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

			country_factory = GenericModelFactory(Country)
			country = country_factory.create_or_get(data={"name": country_name.strip()})
			if country is not None:
				country.save()

			affiliation_factory = GenericModelFactory(Affiliation)
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
				last_name = self.xml_find_items(root=contributor, namespace="any", query=synonym)
				if last_name is not None:
					break

			for synonym in synonyms_for_first_names:
				first_name = self.xml_find_items(root=contributor, namespace="any", query=synonym)
				if first_name is not None:
					break

			affiliation = self.xml_find_items(root=contributor, namespace="any", query="affiliation")

			if last_name is not None and first_name is not None:
				author_factory = GenericModelFactory(Author)
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

	def resolve_full_text(self, storage: Path,  root) -> []:
		collection = self.xml_find_items(root=root, namespace="any", query="collection")
		if collection is None:
			return []
		print(collection)
		resources = self.xml_find_items(root=collection, namespace="any", query="resource", singleton=False)
		if resources is None:
			return []

		full_texts = []

		for i, resource in enumerate(resources):
			file_type = "pdf"
			if 'mime_type' in resource.attrib:
				file_types = resource.attrib['mime_type'].split('/')
				if len(file_types) > 0:
					file_type = file_types[1]
				else:
					file_type = file_types[0]

			resource_request = requests.get(resource.text, headers={
				"Accept": "text/html,application/xhtml+xml,application/pdf,application/xml;q=0.9,image/avif,image/webp",
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"})

			if resource_request.status_code == 200:
				base_file = f"resource_{self.doi.replace("/", "-")}_{i}.{file_type}"
				resource_filename = storage / base_file
				with open(resource_filename, "wb") as resource_file:
					resource_file.write(resource_request.content)

				if file_type.lower() == "pdf":
					try:
						PdfReader(resource_filename)
					except:
						try:
							os.remove(resource_filename)
						except:
							pass
						continue

				full_texts.append((f"storage/full_texts/{base_file}", {
					'url': resource.text,
					'type': FULL_TEXT_TYPES_REVERSE[f"application/{file_type}"],
					'status': "D",  # downloaded
				}))

		return full_texts

	def resolve_keywords(self, query):
		pass

	def add_extra_info_from_json(self, publication) -> Publication:
		# TODO implement
		return publication

	def parse(self, storage: Path) -> None | Publication:
		publication = self.parse_xml(storage)

		# TODO check if extra information is available from the json
		# publication = self.add_extra_info_from_json(publication)

		return publication

