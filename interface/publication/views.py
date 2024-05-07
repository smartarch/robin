import json
import re

import requests
from typing import Any, List

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, BadRequest
from django.views import View
# from django
from django.views.generic import TemplateView, CreateView
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect

# from external apps
from mapping.models import PublicationList, UserPreferences, Mapping
from query.models import QueryPlatform, Query

# from local app
from .models import Publication, Keyword, FullTextAccess, FullText
from .parsers import DOIParser, GenericModelFactory, \
    IEEEXploreParser, ScopusParser  # , IEEEXploreParser, ScopusParser, get_publication_by_doi


def get_publications_by_list_of_doi_list(doi_list: [], extra_infos=None) -> List[Publication]:
    publications = []
    for doi in doi_list:
        # first, check if the DOI already exist in the database
        try:
            publication = Publication.objects.get(doi=doi)
        except ObjectDoesNotExist:
            doi_parser = DOIParser(doi)
            publication = doi_parser.parse()

        if publication is not None and isinstance(publication, Publication):
            publication.save()

            if extra_infos is not None and doi in extra_infos:
                # such as provided abstract
                for key, value in extra_infos[doi].items():
                    if key in publication.__dict__ and len(publication.__dict__[key]) < len(value):
                        publication.__dict__[key] = value
                        publication.save()
                    elif key == "keywords_list":
                        for keyword in value:
                            keyword_parser = GenericModelFactory(Keyword)
                            keyword_object = keyword_parser.create_or_get(data={'keyword': keyword.strip().lower()})
                            keyword_object.save()
                            if len(publication.keywords.filter(id=keyword_object.id)) == 0:
                                publication.keywords.add(keyword_object)
                                publication.save()

            publications.append(publication)
    return publications


def store_publications(publications: List[Publication], publication_list: PublicationList) ->None:
    for publication in publications:
        if publication not in publication_list.publications.all():
            publication_list.publications.add(publication)
            publication_list.save()

            # check if the publication has any FullTextAccess within this mapping
            full_text_access_list = FullTextAccess.objects.filter(mapping=publication_list.mapping) \
                .filter(full_text__publication=publication)

            if len(full_text_access_list) == 0:
                full_text_access_object = FullTextAccess()
                full_text_access_object.mapping = publication_list.mapping
                full_texts = FullText.objects.filter(publication=publication)
                if len(full_texts) == 0:
                    full_text_object = FullText(publication=publication, type="P")
                    full_text_object.save()
                else:
                    full_text_object = full_texts[0]

                full_text_access_object.full_text = full_text_object
                full_text_access_object.save()


class AddPublicationByDOI(LoginRequiredMixin, View):

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not request.POST.__contains__("doi"):
            raise BadRequest("Missing doi in POST data.")

        if request.POST.__contains__("next"):
            next_url = request.POST.get("next")
        else:
            next_url = "/dashboard"

        if request.POST.__contains__("list_id"):
            list_id = int(request.POST.get("list_id"))
            publication_list = get_object_or_404(PublicationList, id=list_id)

            if request.user in publication_list.mapping.reviewers.all():
                # add by bulk
                doi_list = re.split(' |\n|,|;', request.POST.get("doi"))
                publications = get_publications_by_list_of_doi_list(doi_list)
                store_publications(publications, publication_list)

        return redirect(next_url)


class AddPublicationByBIB(LoginRequiredMixin, View):
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        print (request.POST)
        if 'bib_text_file' in request.FILES:
            try:
                bib_text = request.FILES.get('bib_text_file').file.read().decode('utf-8')
            except:
                bib_text = None
        else:
            bib_text = None if 'bib_text' not in request.POST else request.POST.get('bib_text')

        if bib_text is None:
            raise BadRequest("Missing bib_text or bib_file in POST data.")

        if request.POST.__contains__("next"):
            next_url = request.POST.get("next")
        else:
            next_url = "/dashboard"
        if request.POST.__contains__("list_id"):
            list_id = int(request.POST.get("list_id"))
            publication_list = get_object_or_404(PublicationList, id=list_id)

            if request.user in publication_list.mapping.reviewers.all():
                articles = bib_text.split('@')
                compiler = re.compile(r'(?P<key>\w+) = \{(?P<value>.+)\},')

                extra_infos = {}
                doi_list = []
                for article in articles:
                    compiled_article = dict(compiler.findall(article))
                    if "doi" in compiled_article:
                        doi = compiled_article["doi"]
                        doi_list.append(doi)

                        # for other extra information add here
                        if "abstract" in compiled_article:
                            extra_infos[doi] = {"abstract": compiled_article['abstract']}

                        if "keywords" in compiled_article:
                            extra_infos[doi] = {"keywords_list": compiled_article['keywords'].split(',')}

                publications = get_publications_by_list_of_doi_list(doi_list)
                store_publications(publications, publication_list)
        return redirect(next_url)


class AddPublicationsByWeb(LoginRequiredMixin, TemplateView):
    template_name = "publication/web_search.html"

    def get_mappings(self, request: Any) -> dict:
        authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
        mappings = {}
        if authorized_mappings:
            for authorized_mapping in authorized_mappings:
                mappings[authorized_mapping] = PublicationList.objects.filter(mapping=authorized_mapping)
        return mappings

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        context = super().get_context_data(**kwargs)

        context = {
            **super().get_context_data(**kwargs),
            "user": request.user,
            "platforms": QueryPlatform.objects.all(),
            "desired_list": kwargs['list_id'],
            "mappings": self.get_mappings(request),
        }
        return self.render_to_response(context)

    def search_on_web(self, request: Any, *args: Any, **kwargs: Any) -> Any:

        if not request.POST.__contains__("query") and not request.POST.__contains__("source"):
            raise BadRequest("The query and/or sources are not specified")

        query = request.POST.get("query").replace("\"", "\\\"")
        source = int(request.POST.get("source"))
        max_results = request.POST.get("max_results")

        query_platform = get_object_or_404(QueryPlatform.objects.all(), id=source)
        cleaned_params = query_platform.params.replace("%key%", f"\"{query_platform.key}\"")
        cleaned_params = cleaned_params.replace("%query%", f"\"{query}\"")
        cleaned_params = cleaned_params.replace("%max_results%", str(max_results))

        params = dict(json.loads(cleaned_params))
        respond = requests.get(query_platform.url, **params)

        if query_platform.source == "IEEEXplore":
            parser = IEEEXploreParser()
        elif query_platform.source == "Scopus":

            parser = ScopusParser()

        else:
            # for other parsers, please add the Parser class in parser.py
            raise NotImplemented
        publications = parser.parse_text(respond.json())

        if len(publications) > 0:
            # at this moment Scopus manages its own paginator, but we have limited it
            paginator = Paginator(publications, len(publications))
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
        else:
            page_obj = None

        context = {
            **super().get_context_data(**kwargs),
            "user": request.user,
            "platforms": QueryPlatform.objects.all(),
            "source": int(source),
            "page_obj": page_obj,
            "publications": publications,  # to pick from
            "desired_list": kwargs['list_id'],
            "max_results": max_results,
            "mappings": self.get_mappings(request),
            "query": query.replace("\\\"", "\""),
            "no_review": True,
        }

        return self.render_to_response(context)

    def add_from_web(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        current_list = get_object_or_404(PublicationList, id=int(kwargs["list_id"]))

        if "selected_publications" not in request.POST:
            return redirect("publication_list", mapping_id=current_list.mapping.id, list_id=current_list.id)

        doi_list = request.POST.getlist("selected_publications")
        selected_lists = request.POST.getlist("selected_lists")
        print (selected_lists)

        for list_id in selected_lists:
            publication_list = get_object_or_404(PublicationList, id=int(list_id))

            if request.user in publication_list.mapping.reviewers.all():

                extra_infos = {}
                #
                # # for other extra information add here
                # if "abstract" in compiled_article:
                #     extra_infos[doi] = {"abstract": compiled_article['abstract']}
                #
                # if "keywords" in compiled_article:
                #     extra_infos[doi] = {"keywords_list": compiled_article['keywords'].split(',')}

                publications = get_publications_by_list_of_doi_list(doi_list)
                store_publications(publications, publication_list)
        # selected_publication_ids = [int(x) for x in request.POST.getlist("selected_publications")]
        # selected_publication_lists = [int(x) for x in request.POST.getlist("selected_lists")]
        #
        # publications_text = request.POST.get("publications")
        # publications_json = json.loads(publications_text.replace('\'', '\"').replace(': None', ': \"None\"'))
        # for publication_dict in publications_json:
        #     if publication_dict["id"] in selected_publication_ids:
        #         print (publication_dict["doi"])
        #         print(publication_dict["abstract"])

        #
        # source = int(request.POST.get("source_used"))
        # query_text = request.POST.get("queried_text").replace("\"", "\\\"")
        # query_platform = get_object_or_404(QueryPlatform.objects.all(), id=source)
        # query = None
        # json_reader = json.loads(publications.replace('\'','\"').replace(': None', ': \"None\"'))
        # publication_creator = PublicationFactory()
        # already_added = []
        #
        # for publication in json_reader:
        #     clean_publication = publication
        #     if "authors" in clean_publication:
        #         clean_publication["authors"] = clean_publication["authors"]["all"]
        #
        #     if "author_keywords" in clean_publication:
        #         clean_publication["author_keywords"] = clean_publication["author_keywords"]["all"]
        #
        #     if "index_keywords" in clean_publication:
        #         clean_publication["index_keywords"] = clean_publication["index_keywords"]["all"]
        #
        #     if clean_publication['id'] in selected_publication_ids:
        #         try:
        #             new_publication = publication_creator.create(clean_publication)
        #
        #         except:
        #             if "doi" not in clean_publication:
        #                 continue
        #             else:
        #                 already_added_publications = Publication.objects.filter(doi=clean_publication["doi"])
        #                 if not already_added_publications:
        #                     request_data = requests.get(f"https://doi.org/{clean_publication['doi']}", headers={
        #                         "Accept": "application/vnd.citationstyles.csl+json"})
        #                     doi_parser = DOIParser()
        #                     parsed_json = doi_parser.parse(request_data.json())
        #                     new_publication = publication_creator.create(parsed_json)
        #
        #                 else:
        #                     new_publication = already_added_publications[0]
        #
        #         if new_publication:
        #             new_publication.save()
        #
        #
        #         for selected_publication_list in selected_publication_lists:
        #             target_list = get_object_or_404(PublicationList, id=selected_publication_list)
        #
        #             if request.user in target_list.mapping.reviewers.all():
        #                 self.add_publication_to_list(new_publication, target_list)
        #                 # if new_publication not in target_list.publications.all():
        #                 #     target_list.publications.add(new_publication)
        #                 #     target_list.save()
        #
        #         already_added.append(publication)
        #         if not query:
        #             query = Query(query=query_text, user=request.user, platform=query_platform)
        #             query.save()
        #         query.found_publications.add(new_publication)
        #
        # if query:
        #     query.results = json.dumps(already_added)
        #     query.save()

        return redirect("publication_list", mapping_id=current_list.mapping.id, list_id=current_list.id)

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        print (request.POST)
        if request.POST.__contains__("search_on_web"):
            return self.search_on_web(request, *args, **kwargs)

        elif request.POST.__contains__("add_from_web"):
            return self.add_from_web(request, *args, **kwargs)

        else:
            return self.get(request, *args, **kwargs)

