from typing import List, Any
import re

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Model
from requests import Response
import xml.etree.ElementTree as eT

from .constants import FULL_TEXT_TYPES_REVERSE
from .models import Source, Country, Affiliation, Author, Venue, Keyword, Publication, FullText


ARTICLE_TYPES = {
	"article": "Journal Article",
	"Early Access Articles": "Article",
	"book": "(Whole) Book",
	"Book": "(Whole) Book",
	"Book Series": "(Whole) Book",
	"booklet": "(Whole) Booklet",
	"conference": "Conference Paper",
	"Conferences": "Conference Paper",
	"conference-proceeding": "Conference Paper",
	"Conference Proceeding": "Conference Paper",
	"proceedings-article": "Conference Paper",
	"inbook": "Book Section",
	"incollection": "Collection Paper",
	"inproceedings": "Conference Paper",
	"Journal-article": "Journal Article",
	"journal-article": "Journal Article",
	"Journal": "Journal Article",
	"Journals": "Journal Article",
	"manual": "Technical Manual",
	"masterthesis": "Master Thesis",
	"misc": "Miscellaneous",
	"phdthesis": "Ph.D Thesis",
	"proceedings": "(Whole) Conference Proceeding",
	"techreport": "Technical Report",
	"unpublished": "Unpublished",
	"other": "other",
	"Magazines": "Magazines",
	None: None,
}


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
				return self.model.objects.filter(publication=data['publication']).get(type=data['type'])

			return None

		except ObjectDoesNotExist:
			print(f"object was not found for {self.model}")
			return None

	def create_or_get(self, data: dict) -> models.Model | None:
		instance = self.find_object(data)
		if instance is None:
			return self.model(**data)

		return instance




def find_article_type(key):
	if key in ARTICLE_TYPES:
		return ARTICLE_TYPES[key]
	else:
		return "other"



class Parser:  # generic parser
	def parse_authors(self, text: Any) -> Any:
		raise NotImplemented

	def parse_affiliation(self, text: Any) -> Any:
		raise NotImplemented

	def parse(self) -> None | Publication:
		raise NotImplementedError

	@staticmethod
	def try_get(msg: dict, key: str) -> Any:
		if msg and key in msg:
			return msg[key]
		else:
			return None

	@staticmethod
	def try_access(msg: list, index: int) -> Any:
		if msg and index < len(msg):
			return msg[index]
		else:
			return None

	@staticmethod
	def try_lower(msg: str | None) -> Any:
		if msg:
			return msg.lower()
		else:
			return None

	def parse_text(self, text: Any) -> Any:
		raise NotImplemented

#
# class DOIParser(Parser):
# 	def parse_affiliation(self, author_affiliation: Any) -> dict:
# 		if not author_affiliation:
# 			return {}
# 		if isinstance(author_affiliation, dict):
# 			code = author_affiliation['name']
# 		else:
# 			code = author_affiliation.split(',')
# 		if len(code) > 1:
# 			return {
# 				"institute": ", ".join(code[:-1]),
# 				"country": {
# 					"name": code[-1],
# 				}
# 			}
# 		return {}
#
# 	def parse_authors(self, authors: Any) -> list:
# 		return [{
# 			"first_name": author["given"] if "given" in author else Parser.try_get(msg=author, key="name"),
# 			"last_name": author["family"] if "family" in author else Parser.try_get(msg=author, key="name"),
# 			"affiliation": self.parse_affiliation(Parser.try_access(
# 				Parser.try_get(msg=author, key="affiliation"), index=0)),
# 		}
# 			for author in authors
# 		]
#
# 	def parse(self, txt: Any) -> Any:
# 		return {
# 			"title": txt["title"],
# 			"clean_title": re.sub('[^a-zA-Z0-9]+', '', str(txt["title"])).lower(),
# 			"year": txt["published"]["date-parts"][0][0] if "published" in txt else txt["issued"]["date-parts"][0][0],
# 			"doi": txt["DOI"],
# 			"url": Parser.try_get(msg=txt, key="URL"),
# 			"citations": Parser.try_get(msg=txt, key="is-referenced-by-count"),
# 			"abstract": Parser.try_get(msg=txt, key="abstract"),
# 			"source": Parser.try_get(msg=txt, key="source"),
# 			"event": {
# 				"name": txt["container-title"] if "container-title" in txt else "NO_EVENT",
# 				"type": find_article_type(Parser.try_lower(Parser.try_get(msg=txt, key="type"))),
# 				"publisher": txt["publisher"],
# 				"acronym": Parser.try_get(msg=txt, key="short-container-title"),
# 				"volume": Parser.try_get(msg=txt, key="volume"),
# 				"number": Parser.try_get(msg=txt, key="issue"),
# 			},
# 			"authors": self.parse_authors(txt["author"]),
# 		}
#
#
# class ParseBibText(Parser):
# 	def parse_affiliation(self, text: Any) -> Any:
# 		return {}
#
# 	def parse_authors(self, authors: str) -> list:
# 		authors_list = authors.split(" and ")
# 		author_names = []
# 		for author in authors_list:
# 			full_name = re.findall("(.*), (.*)", author)
# 			if len(full_name) == 0:
# 				last_name, first_name = author, "N/A"
# 			else:
# 				last_name, first_name = full_name[0]
# 			author_names.append({
# 				"first_name": first_name.strip().strip('}').strip('{'),
# 				"last_name": last_name.strip().strip('}').strip('{')
# 			})
# 		return author_names
#
# 	def parse_keywords(self, keyword_list: str) -> list | None:
# 		if keyword_list:
# 			return [{"name": key.strip()} for key in keyword_list.split(',')]
#
# 		return []
#
# 	def parse(self, text: Any) -> Any:
# 		"""
# 			This method converts bib text to
# 			Please check https://www.bibtex.com/g/bibtex-format/
# 			:param text: the bibtext
# 			:return: a list of json (dictionary) objects
# 			"""
#
# 		results = []
# 		spliter = re.split("\s*\@\w+\{", text)
# 		if len(spliter) < 2:
# 			return []
# 		else:
# 			spliter = spliter[1:]
# 		article_types = re.findall("\s*\@(\w+)\{", text)
# 		for data, article_type in zip(spliter, article_types):
# 			parsed_attributes = re.findall("(?:.*)\s(\w+)\s=\s\{([\S\s]+?(?=\},))", data)
#
# 			if article_type.lower() not in ARTICLE_TYPES:
# 				continue
#
# 			parsed_dict = {
# 				attribute[0].strip().lower(): ''.join(attribute[1:])
#
# 				for attribute in parsed_attributes
# 			}
# 			entity = {
# 				"source": "BibText",
# 				**{
# 					key: self.try_get(msg=parsed_dict, key=key)
# 					for key in ["title", "doi", "url", "abstract"]
# 				},
# 				"clean_title": re.sub('[^a-zA-Z0-9]+', '', str(parsed_dict["title"])).lower(),
# 				"year": parsed_dict["year"] if "year" in parsed_dict else re.findall("(\d{4})", parsed_dict["date"])[0],
# 				"event": {
# 					"type": find_article_type(article_type.lower()),
# 					"name": parsed_dict["journaltitle"] if "journaltitle" in parsed_dict else parsed_dict["booktitle"]
# 					if "booktitle" in parsed_dict else f"OTHER -> {self.try_get(msg=parsed_dict, key='isbn')}",
# 					"acronym": self.try_get(msg=parsed_dict, key="shortjournal"),
# 					**{
# 						key: self.try_get(msg=parsed_dict, key=key)
# 						for key in ["volume", "number", "publisher"]
# 					},
#
# 				},
# 				"authors": self.parse_authors(parsed_dict["author"]),
# 				"index_keywords": self.parse_keywords(Parser.try_get(msg=parsed_dict, key="keywords")),
# 				"author_keywords": [],
#
# 			}
# 			results.append(entity)
#
# 		return results
#
#


class IEEEXploreParser(Parser):
	def parse_affiliation(self, author_affiliation: Any) -> dict:
		if not author_affiliation:
			return {}
		code = author_affiliation.split(',')
		if code:
			return {
				"institute": ", ".join(code[:-1]).replace('\'', ''),
				"country": {
					"name": code[-1].replace('\'', ''),
				}
			}
		return {}

	def parse_authors(self, author_list: Any) -> Any:
		authors = []
		for author in author_list:
			full_name = author['full_name'].split(' ')
			authors.append({
				"first_name": full_name[0].replace('\'', ''),
				"last_name": full_name[-1].replace('\'', ''),
				"affiliation": self.parse_affiliation(self.try_get(msg=author, key="affiliation"))
			})

		return authors

	def parse_keywords(self, keyword_list: dict) -> list | None:
		if keyword_list and "terms" in keyword_list:
			return [{"name": keyword.replace('\'', '')} for keyword in keyword_list["terms"]]
		return []


	def parse_text(self, text: Any) -> Any:
		entities = text["articles"]
		publications = []
		for i, entry in enumerate(entities):
			doi = self.try_get(msg=entry, key='doi'),
			if doi is not None:
				publications.append({
					"source": "IEEEXplore",
					"title": entry['title'].replace('\'', ''),
					"clean_title": re.sub('[^a-zA-Z0-9]+', '', str(entry["title"])).lower(),
					"id": i,
					"doi": self.try_get(msg=entry, key='doi'),
					"event": {
						"name": entry["publication_title"].replace('\'', ''),
						"article_type": find_article_type(self.try_get(msg=entry, key="content_type")),
						"volume": self.try_get(msg=entry, key="volume"),
						"number": self.try_get(msg=entry, key="issue"),
						"publisher": self.try_get(msg=entry, key="publisher"),
					},
					"authors": {"all": self.parse_authors(entry["authors"]["authors"])},
					"year": entry["publication_year"],
					"abstract": self.try_get(msg=entry, key="abstract").replace('\'', ''),
					"citations": self.try_get(msg=entry, key="citing_paper_count"),
					"index_keywords": {
						"all": self.parse_keywords(self.try_get(self.try_get(entry, "index_terms"), "ieee_terms")),
					},
					"author_keywords": {
						"all": self.parse_keywords(self.try_get(self.try_get(entry, "index_terms"), "author_terms")),
					},
				})
		return publications


class ScopusParser(Parser):
	def parse_affiliation(self, text: Any) -> Any:
		pass

	def parse_authors(self, text: Any) -> Any:
		pass

	def parse_text(self, text: Any) -> Any:
		entities = text["search-results"]["entry"]
		publications = []
		for i, entry in enumerate(entities):
			doi = self.try_get(msg=entry, key='doi'),
			if doi is not None:
				publications.append({
					"title": entry['dc:title'],
					"clean_title": re.sub(r'[^a-zA-Z0-9]+', '', str(entry["dc:title"])).lower(),
					"id": i,
					"doi": self.try_get(msg=entry, key='prism:doi'),
					"url": f"http://doi.org/{self.try_get(msg=entry, key='prism:doi')}",
					"article_type": find_article_type(self.try_get(msg=entry, key='prism:aggregationType')),
					"year": int(re.findall(r".*(\d\d\d\d).*", self.try_get(msg=entry, key="prism:coverDate"))[0]),
				})
		return publications


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
			print("The server is down or not accepting xml")

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

	def parse_xml(self) -> None | Publication:
		if self.xml_resp.status_code != 200:
			print("doi not found")
			return None

		xml_data = self.xml_resp.text

		try:
			root = eT.fromstring(xml_data)
		except eT.ParseError as e:
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
		full_texts = self.resolve_full_text(publication)
		for full_text in full_texts:
			full_text_factory = GenericModelFactory(FullText)
			full_text_object = full_text_factory.create_or_get({"publication": publication_object, **full_text})

			if full_text_object is not None and isinstance(full_text_object, FullText):
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
					journal.type = "J"

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

	def resolve_full_text(self, root) -> []:
		collection = self.xml_find_items(root=root, namespace="any", query="collection")
		if collection is None:
			return []

		resources = self.xml_find_items(root=collection, namespace="any", query="resource", singleton=False)
		if resources is None or len(resources) == 0:
			return [{
				'url': "",
				'type': "P",
			}]

		full_texts = []

		for i, resource in enumerate(resources):
			file_type = "pdf"
			if 'mime_type' in resource.attrib:
				file_types = resource.attrib['mime_type'].split('/')
				if len(file_types) > 0:
					file_type = file_types[1]
				else:
					file_type = file_types[0]

			full_texts.append({
				'url': resource.text,
				'type': FULL_TEXT_TYPES_REVERSE[f"application/{file_type}"],
			})

		return full_texts

	def resolve_keywords(self, query):
		pass

	def add_extra_info_from_json(self, publication) -> Publication:
		# TODO implement
		return publication

	def parse(self) -> None | Publication:
		publication = self.parse_xml()

		# TODO check if extra information is available from the json
		# publication = self.add_extra_info_from_json(publication)

		return publication
