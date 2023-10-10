from django.db import models
from django.db.models import Q
from .models import Source, Country, Affiliation, Author, Event, Publication, Keywords, FullText
from django.core.files.base import ContentFile
import requests


class Factory:

	_model: type(models.Model) = None
	_lookup: {} = None

	def __init__(self, model: type(models.Model), _lookup: {} = None, union: bool = True) -> None:
		self._model = model
		self._lookup = _lookup
		self._union = union

	def create(self, data: dict) -> Publication | Event | Author | Affiliation | Keywords | Source | Country:
		# self._alike_fields is a subset of data
		instances = None
		if self._lookup:
			query = None
			for key, value in self._lookup.items():
				assert value in data, f"The (given) data is missing '{value}' key."
				new_query = Q(**{key: data[value]})
				if query:
					if self._union:
						query = query | new_query
					else:
						query = query & new_query
				else:
					query = new_query

			instances = self._model.objects.filter(query)

		instance = self._model() if not instances else instances[0]
		for key, value in data.items():
			if value is not None and value != "" and value != 0:
				instance.__dict__[key] = value

		return instance


class PublicationFactory:

	def __init__(self) -> None:
		self.source = Factory(Source, {"name__iexact": "name"})
		self.country = Factory(Country, {"name__iexact": "name", "other_forms__icontains": "name"})
		self.affiliation = Factory(Affiliation, {"institute__icontains": "institute"})
		self.author = Factory(Author,
			{"last_name__iexact": "last_name", "first_name__icontains": "first_name"}, union=False)
		self.event = Factory(Event, {"name__icontains": "name", "publisher__iexact": "publisher"}, union=False)
		self.keywords = Factory(Keywords, {"name__iexact": "name"})
		self.publication = Factory(Publication, {"clean_title__iexact": "clean_title"})
		self.publication = Factory(Publication, {"clean_title__iexact": "clean_title"})

	def resolve_keywords(self, keywords: list) -> [Keywords]:
		created_keywords = []
		for keyword in keywords:
			new_keyword = self.keywords.create({"name": keyword['name']})
			new_keyword.save()
			created_keywords.append(new_keyword)
		return created_keywords

	def resolve_authors(self, authors: list) -> [Author]:
		created_authors = []
		for author in authors:
			new_author = self.author.create({"first_name": author["first_name"], "last_name": author["last_name"]})
			if "affiliation" in author:
				if "institute" in author["affiliation"]:
					new_affiliation = self.affiliation.create({"institute": author["affiliation"]["institute"]})
					new_country = self.country.create({"name": author["affiliation"]["country"]["name"]})
					new_country.save()
					new_affiliation.country = new_country
					new_affiliation.save()
					new_author.affiliation = new_affiliation

			new_author.save()
			created_authors.append(new_author)
		return created_authors

	def create(self, data: dict) -> Publication:
		new_publication = self.publication.create({
			k: data[k] for k in ["title", "clean_title", "year", "doi", "abstract", "citations", "url"]
		})
		new_event = self.event.create(data["event"])
		new_event.save()

		new_source = self.source.create({"name": data["source"]})
		new_source.save()

		new_publication.source = new_source
		new_publication.event = new_event
		new_publication.save()

		if "author_keywords" in data:
			keywords = self.resolve_keywords(data["author_keywords"])
			for key in keywords:
				if key not in new_publication.author_keywords.all():
					new_publication.author_keywords.add(key)

		if "index_keywords" in data:
			keywords = self.resolve_keywords(data["index_keywords"])
			for key in keywords:
				if key not in new_publication.index_keywords.all():
					new_publication.index_keywords.add(key)

		for author in self.resolve_authors(data["authors"]):
			if author not in new_publication.authors.all():
				new_publication.authors.add(author)

		new_publication.save()
		return new_publication


def create_publication(data: dict) -> Publication:

	sources = Source.objects.filter(name="CrossRef")
	if sources:
		source = sources[0]
	else:
		source = Source(name="CrossRef")
		source.save()

	publication = Publication(source=source)
	for direct_item in ["doi", "title", "abstract", "year"]:
		publication.__dict__[direct_item] = data[direct_item]

	events = Event.objects.filter(name=data["event"]["name"])
	if events:
		event = events[0]
	else:
		event = Event()
		for direct_item in ["type", "name", "volume", "acronym", "number"]:
			if  data["event"][direct_item]:
				event.__dict__[direct_item] = data["event"][direct_item]
		event.save()

	publication.event = event
	publication.save()

	for author_data in data["authors"]:
		def_author = Author.objects.filter(ORCID=author_data["ORCID"])
		p_author = Author.objects.filter(last_name=author_data["last_name"]).filter(first_name=author_data["first_name"])

		if def_author or p_author:
			if def_author:
				author = def_author[0]
			else:
				author = p_author[0]
		else:
			author = Author(first_name=author_data["first_name"], last_name=author_data["last_name"], ORCID=author_data["ORCID"])
			if "affiliation" in author_data and author_data["affiliation"]:
				affiliation_text = author_data["affiliation"].split(',')
				affiliations = Affiliation.objects.filter(institute=affiliation_text[0])
				if affiliations:
					author.affiliation = affiliations[0]
				else:
					if len(affiliation_text) > 1:
						affiliation = Affiliation(institute=affiliation_text[0])
						countries = Country.objects.filter(affiliation_text[-1])
						if countries:
							country = countries[0]
						else:
							country = Country(name=affiliation_text[-1])
							country.save()
						affiliation.country = country
						affiliation.save()
						author.affiliation = affiliation
			author.save()
		if author not in publication.authors.all():
			publication.authors.add(author)
			publication.save()

	def create_fulltext(code, t, extension) -> None:
		for text in data["full_text"][code]:
			response = requests.get(text)
			if response.ok:
				with open(f"media/full_text/paper_{publication.id}.{extension}", "wb") as resource:
					resource.write(response.content)
					full_text = FullText(url=text, resource=resource, type=t, publication=publication)
					full_text.save()
			else:
				full_text = FullText(url=text, type=t, publication=publication)
				full_text.save()

	create_fulltext("text/html", "H", "html")
	create_fulltext("application/pdf", "P", "pdf")
	create_fulltext("text/plain", "T", "txt")
	create_fulltext("text/xml", "X", "xml")
	return publication

