import requests
import re
from xml.parsers.expat import ExpatError
import xmltodict
import re
from typing import Any

ARTICLE_TYPES = {
    "article": "Journal Article",
    "book": "(Whole) Book",
    "Book Series": "(Whole) Book",
    "booklet": "(Whole) Booklet",
    "conference": "Conference Paper",
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
    None: None,
}


class Parser:   # generic parser
    def parse_authors(self, text: Any) -> Any:
        raise NotImplemented

    def parse_affiliation(self, text: Any) -> Any:
        raise NotImplemented

    def parse(self, text: Any) -> Any:
        raise NotImplemented

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
    def try_lower(msg: str|None) -> Any:
        if msg:
            return msg.lower()
        else:
            return None

class DOIParser (Parser):
    def parse_affiliation(self, author_affiliation: Any) -> dict:
        if not author_affiliation:
            return {}
        if isinstance(author_affiliation, dict):
            code = author_affiliation['name']
        else:
            code = author_affiliation.split(',')
        if len(code) > 1:
            return {
                "institute": ", ".join(code[:-1]),
                "country": {
                    "name": code[-1],
                }
            }
        return {}

    def parse_authors(self, authors: Any) -> list:
        return [{
            "first_name": author["given"] if "given" in author else Parser.try_get(msg=author, key="name"),
            "last_name": author["family"] if "family" in author else Parser.try_get(msg=author, key="name"),
            "affiliation": self.parse_affiliation(Parser.try_access(
                Parser.try_get(msg=author, key="affiliation"), index=0)),
            }
            for author in authors
        ]

    def parse(self, txt: Any) -> Any:
        return {
            "title": txt["title"],
            "clean_title": re.sub('[^a-zA-Z0-9]+', '', str(txt["title"])).lower(),
            "year": txt["published"]["date-parts"][0][0] if "published" in txt else txt["issued"]["date-parts"][0][0],
            "doi": txt["DOI"],
            "url": Parser.try_get(msg=txt, key="URL"),
            "citations": Parser.try_get(msg=txt, key="is-referenced-by-count"),
            "abstract": Parser.try_get(msg=txt, key="abstract"),
            "source": Parser.try_get(msg=txt, key="source"),
            "event": {
                "name": txt["container-title"] if "container-title" in txt else "NO_EVENT",
                "type": ARTICLE_TYPES[Parser.try_lower(Parser.try_get(msg=txt, key="type"))],
                "publisher": txt["publisher"],
                "acronym": Parser.try_get(msg=txt, key="short-container-title"),
                "volume": Parser.try_get(msg=txt, key="volume"),
                "number": Parser.try_get(msg=txt, key="issue"),
            },
            "authors": self.parse_authors(txt["author"]),
    }

class ParseBibText (Parser):
    def parse_affiliation(self, text: Any) -> Any:
        return {}

    def parse_authors(self, authors: str) -> list:
        authors_list = authors.split(" and ")
        author_names = []
        for author in authors_list:
            full_name = re.findall("(.*), (.*)", author)
            if len(full_name) == 0:
                last_name, first_name = author, "N/A"
            else:
                last_name, first_name = full_name[0]
            author_names.append({
                "first_name": first_name.strip().strip('}').strip('{'),
                "last_name": last_name.strip().strip('}').strip('{')
            })
        return author_names

    def parse_keywords(self, keyword_list: str) -> list | None:
        if keyword_list:
            return [{"name": key.strip()} for key in keyword_list.split(',')]

        return []

    def parse(self, text: Any) -> Any:
        """
            This method converts bib text to
            Please check https://www.bibtex.com/g/bibtex-format/
            :param text: the bibtext
            :return: a list of json (dictionary) objects
            """

        results = []
        spliter = re.split("\s*\@\w+\{", text)
        if len(spliter) < 2:
            return []
        else:
            spliter = spliter[1:]
        article_types = re.findall("\s*\@(\w+)\{", text)
        for data, article_type in zip(spliter, article_types):
            parsed_attributes = re.findall("(?:.*)\s(\w+)\s=\s\{([\S\s]+?(?=\},))", data)

            if article_type.lower() not in ARTICLE_TYPES:
                continue

            parsed_dict = {
                attribute[0].strip().lower(): ''.join(attribute[1:])

                for attribute in parsed_attributes
            }
            entity = {
                "source": "BibText",
                **{
                    key: self.try_get(msg=parsed_dict, key=key)
                    for key in ["title", "doi", "url", "abstract"]
                },
                "clean_title": re.sub('[^a-zA-Z0-9]+', '', str(parsed_dict["title"])).lower(),
                "year": parsed_dict["year"] if "year" in parsed_dict else re.findall("(\d{4})", parsed_dict["date"])[0],
                "event": {
                    "type": ARTICLE_TYPES[article_type.lower()],
                    "name": parsed_dict["journaltitle"] if "journaltitle" in parsed_dict else parsed_dict["booktitle"]
                    if "booktitle" in parsed_dict else f"OTHER -> {self.try_get(msg=parsed_dict, key='isbn')}",
                    "acronym": self.try_get(msg=parsed_dict, key="shortjournal"),
                    **{
                        key: self.try_get(msg=parsed_dict, key=key)
                        for key in ["volume", "number", "publisher"]
                    },

                },
                "authors": self.parse_authors(parsed_dict["author"]),
                "index_keywords": self.parse_keywords(Parser.try_get(msg=parsed_dict, key="keywords")),
                "author_keywords": [],

            }
            results.append(entity)

        return results


class IEEEXploreParser(Parser):
    def parse_affiliation(self, author_affiliation: Any) -> dict:
        if not author_affiliation:
            return {}
        code = author_affiliation.split(',')
        if code:
            return {
                "institute": ", ".join(code[:-1]).replace('\'',''),
                "country": {
                    "name": code[-1].replace('\'',''),
                }
            }
        return  {}

    def parse_authors(self, author_list: Any) -> Any:
        authors = []
        for author in author_list:
            full_name = author['full_name'].split(' ')
            authors.append({
                "first_name": full_name[0].replace('\'',''),
                "last_name": full_name[-1].replace('\'',''),
                "affiliation": self.parse_affiliation(self.try_get(msg=author, key="affiliation"))
            })

        return authors

    def parse_keywords(self, keyword_list: dict) -> list | None:
        if keyword_list and "terms" in keyword_list:
            return [{"name": keyword.replace('\'', '')} for keyword in keyword_list["terms"]]
        return []

    def parse(self, text: Any) -> Any:
        entities = text["articles"]
        publications = []
        for i, entry in enumerate(entities):
            publications.append({
                "source": "IEEEXplore",
                "title": entry['title'].replace('\'',''),
                "clean_title": re.sub('[^a-zA-Z0-9]+', '', str(entry["title"])).lower(),
                "id": i,
                "doi": self.try_get(msg=entry, key='doi'),
                "event": {
                    "name": entry["publication_title"].replace('\'',''),
                    "article_type": ARTICLE_TYPES[self.try_get(msg=entry, key="content_type")],
                    "volume": self.try_get(msg=entry, key="volume"),
                    "number": self.try_get(msg=entry, key="issue"),
                    "publisher": self.try_get(msg=entry, key="publisher"),
                },
                "authors": {"all": self.parse_authors(entry["authors"]["authors"])},
                "year": entry["publication_year"],
                "abstract": self.try_get(msg=entry, key="abstract").replace('\'',''),
                "citations": self.try_get(msg=entry, key="citing_paper_count"),
                "index_keywords": {
                    "all": self.parse_keywords(self.try_get(self.try_get(entry, "index_terms"),"ieee_terms")),
                },
                "author_keywords": {
                    "all": self.parse_keywords(self.try_get(self.try_get(entry, "index_terms"),"author_terms")),
                },
            })
        return publications


class ScopusParser(Parser):
    def parse_affiliation(self, text: Any) -> Any:
        pass

    def parse_authors(self, text: Any) -> Any:
        pass

    def parse(self, text: Any) -> Any:
        entities = text["search-results"]["entry"]
        publications = []
        for i, entry in enumerate(entities):
            publications.append({
                "title": entry['dc:title'],
                "clean_title": re.sub('[^a-zA-Z0-9]+', '', str(entry["dc:title"])).lower(),
                "id": i,
                "doi": self.try_get(msg=entry, key='prism:doi'),
                "url": f"http://doi.org/{self.try_get(msg=entry, key='prism:doi')}",
                "article_type": ARTICLE_TYPES[self.try_get(msg=entry, key='prism:aggregationType')],
                "year": int(re.findall(".*(\d\d\d\d).*", self.try_get(msg=entry, key="prism:coverDate"))[0]),
            })
        return publications


def get_publication_by_doi(doi: str) -> dict | int:
    url = f"https://dx.doi.org/{doi}"
    req = requests.get(url, headers={"Accept": "application/vnd.crossref.unixsd+xml"})
    if req.ok:
        try:
            xml_dict = xmltodict.parse(req.content)
        except ExpatError:
            return 0

        if "crossref_result" in xml_dict \
                and "query_result" in xml_dict["crossref_result"] \
                and "body" in xml_dict["crossref_result"]["query_result"] \
                and "query" in xml_dict["crossref_result"]["query_result"]["body"] \
                and xml_dict["crossref_result"]["query_result"]["body"]["query"]["@status"] == "resolved" \
                and "doi_record" in xml_dict["crossref_result"]["query_result"]["body"]["query"] \
                and "crossref" in xml_dict["crossref_result"]["query_result"]["body"]["query"]["doi_record"]:

            record = xml_dict["crossref_result"]["query_result"]["body"]["query"]["doi_record"]["crossref"]

            publication_types = [k for k in record.keys() if re.match("[jounral|conferance|book]", k)]
            if not publication_types or len(publication_types) > 1:
                return 1

            publication_venue_type = publication_types[0]

            publication = [k for k in record[publication_venue_type].keys() if
                           re.match("conference_paper|journal_article|content_item", k)]

            if not publication or len(publication) > 1:
                return 2

            current_publication = record[publication_venue_type][publication[0]]
            contributors_dict = current_publication["contributors"]
            publication_date_dict = current_publication["publication_date"]
            collection = current_publication["doi_data"]['collection']
            abstract = current_publication["jats:abstract"][
                "jats:p"] if "jats:abstract" in current_publication else ""
            title = current_publication["titles"]["title"]

            authors = []
            if isinstance(contributors_dict["person_name"], dict):
                contributors_list = [contributors_dict["person_name"]]
            else:
                contributors_list = contributors_dict["person_name"]
            for contributor in contributors_list:
                authors.append({
                    "first_name": contributor["given_name"],
                    "last_name": contributor["surname"],
                    "affiliation": contributor["affiliation"] if "affiliation" in contributor else None,
                    "ORCID": contributor["ORCID"] if "ORCID" in contributor else None,
                })

            def to_list(_data, _key):
                if isinstance(_data, dict):
                    return [_data[_key]]
                else:
                    return [d[_key] for d in _data]

            year = min([int(year) for year in to_list(publication_date_dict, "year")])

            items = to_list(collection, 'item')
            resources = []
            for item in items:
                resources.extend(to_list(item, "resource"))

            full_text = {
                'text/html': [],
                'application/pdf': [],
                'text/xml': [],
                'text/plain': [],
            }

            for resource in resources:
                if '@mime_type' in resource and resource['@mime_type'] in full_text:
                    full_text[resource['@mime_type']].append(resource['#text'])
                else:
                    full_text['application/pdf'].append(resource)

            event = record[publication_venue_type]
            if publication_venue_type == "journal":
                journal = event["journal_metadata"]
                event_type = "Journal Article"
                event_name = journal["full_title"]
                event_acronym = journal["abbrev_title"] if "abbrev_title" in journal else ""
                event_number = journal["issue"] if "issue" in journal else None
                event_volume = journal["journal_volume"]["volume"] if "journal_volume" in journal else None
                publisher = journal["publisher"]["publisher_name"] if "publisher" in journal else ""

            elif publication_venue_type == "conference":
                proceedings = event["proceedings_metadata"]
                event_type = "Conference Proceedings"
                event_name = proceedings["proceedings_title"]
                publisher = proceedings["publisher"]["publisher_name"]
                event_acronym = ""
                event_number = None
                event_volume = None
            else:
                book_section = event["book_series_metadata"]
                event_type = "Book Section"
                event_name = book_section["titles"]['title']
                publisher = book_section["series_metadata"]["titles"]['title']
                event_acronym = None
                event_number = None
                event_volume = book_section["volume"]

            return {
                "authors": authors,
                "event": {
                    "type": event_type,
                    "name": event_name,
                    "acronym": event_acronym,
                    "number": event_number,
                    "volume": event_volume,
                    "publisher": publisher,
                },

                "full_text": full_text,
                "title": title,
                "year": year,
                "doi": doi,
                "abstract": abstract
            }
        return 3
    return req.status_code