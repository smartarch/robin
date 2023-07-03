from typing import Any
import json
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.template import loader
from django.db.models import Q
from django.views.generic import TemplateView, View, CreateView
from .models import Publication, Keywords
from django.http import HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
import requests
from mapping.models import PublicationList, UserPreferences, Mapping
from query.models import QueryPlatform, Query
from django.shortcuts import get_object_or_404, redirect
# parsers
from .parsers import DOIParser, ParseBibText, IEEEXploreParser, ScopusParser
from .factories import PublicationFactory
import re
from urllib import parse

class AddPublicationByDOI(LoginRequiredMixin, CreateView):
    model = Publication

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not request.POST.__contains__("doi"):
            return HttpResponseBadRequest("The DOI is not specified", status=406)  # 406: Not acceptable

        if request.POST.__contains__("next"):
            next_url = request.POST.get("next")
        else:
            next_url = "/dashboard"

        doi = request.POST.get("doi")
        already_added_publications = Publication.objects.filter(doi=doi)
        if len(already_added_publications) > 0:
            new_publication = already_added_publications[0]
        else:
            request_data = requests.get(f"https://doi.org/{doi}", headers={
                "Accept": "application/vnd.citationstyles.csl+json"})
            doi_parser = DOIParser()
            parsed_json = doi_parser.parse(request_data.json())

            publication_creator = PublicationFactory()
            new_publication = publication_creator.create(parsed_json)
            if new_publication:
                new_publication.save()

        if request.POST.__contains__("list_id"):
            list_id = int(request.POST.get("list_id"))
            publication_list = get_object_or_404(PublicationList, id=list_id)

            if request.user in publication_list.mapping.reviewers.all():
                if new_publication not in publication_list.publications.all():
                    publication_list.publications.add(new_publication)

        return redirect(next_url, permanent=True)


class AddPublicationsByBibText(LoginRequiredMixin, View):
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not request.POST.__contains__("bib_text") and not request.FILES:
            return HttpResponseBadRequest("The bib text is not specified", status=406)  # 406: Not acceptable

        if request.POST.__contains__("next"):
            next_url = request.POST.get("next")
        else:
            next_url = "/dashboard"

        sources = {
            **{a.name: a for a in request.FILES.getlist("bib_text_files")},
            'direct_text': request.POST.get("bib_text").split('\n')
        }

        for filename, content in sources.items():
            sources[filename] = "\n".join([line if isinstance(line, str) else line.decode("UTF-8") for line in content])

        publication_creator = PublicationFactory()
        for source, publications in sources.items():
            parser = ParseBibText()
            try:
                temporary_jsons = parser.parse(publications)
                for temporary_json in temporary_jsons:
                    new_publication = publication_creator.create(temporary_json)

                    if new_publication:
                        new_publication.save()

                    if request.POST.__contains__("list_id"):
                        list_id = int(request.POST.get("list_id"))
                        publication_list = get_object_or_404(PublicationList, id=list_id)

                        if request.user in publication_list.mapping.reviewers.all():
                            if new_publication not in publication_list.publications.all():
                                publication_list.publications.add(new_publication)
            except:
                return HttpResponseBadRequest("The bib text is not correct", status=406)  # 406: Not acceptable
        return redirect(next_url, permanent=True)


class AddPublicationsByWeb(LoginRequiredMixin, TemplateView):
    template_name = "publication/web_search.html"

    def get_mappings(self, request: Any)-> dict:
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
            return HttpResponseBadRequest("The query and/or sources are not specified", status=406)

        query = request.POST.get("query").replace("\"", "\\\"")
        source = int(request.POST.get("source"))
        max_results = request.POST.get("max_results")

        query_platform = get_object_or_404(QueryPlatform.objects.all(), id=source)
        cleaned_params = query_platform.params.replace("%key%", f"\"{query_platform.key}\"")
        cleaned_params = cleaned_params.replace("%query%", f"\"{query}\"")
        cleaned_params = cleaned_params.replace("%max_results%", str(max_results))
        try:
            params = dict(json.loads(cleaned_params))
            respond = requests.get(query_platform.url, **params)
            if query_platform.source == "IEEEXplore":
                parser = IEEEXploreParser()
            elif query_platform.source == "Scopus":

                parser = ScopusParser()

            else:
                # for other parsers, please add the Parser class in parser.py
                raise NotImplemented
            publications = parser.parse(respond.json())

        except:
            publications = []

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
            "query": query.replace("\\\"", "\"")
        }

        return self.render_to_response(context)

    def add_from_web(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        selected_publication_ids = [int(x) for x in request.POST.getlist("selected_publications")]
        selected_publication_lists = [int(x) for x in request.POST.getlist("selected_lists")]

        publications = request.POST.get("publications")
        source = int(request.POST.get("source_used"))
        query_text = request.POST.get("queried_text").replace("\"", "\\\"")
        query_platform = get_object_or_404(QueryPlatform.objects.all(), id=source)
        query = None

        json_reader = json.loads(publications.replace('\'','\"').replace(': None', ': \"None\"'))
        publication_creator = PublicationFactory()
        already_added = []

        for publication in json_reader:
            clean_publication = publication
            if "authors" in clean_publication:
                clean_publication["authors"] = clean_publication["authors"]["all"]

            if "author_keywords" in clean_publication:
                clean_publication["author_keywords"] = clean_publication["author_keywords"]["all"]

            if "index_keywords" in clean_publication:
                clean_publication["index_keywords"] = clean_publication["index_keywords"]["all"]

            if clean_publication['id'] in selected_publication_ids:
                try:
                    new_publication = publication_creator.create(clean_publication)

                except:
                    if "doi" not in clean_publication:
                        continue
                    else:
                        already_added_publications = Publication.objects.filter(doi=clean_publication["doi"])
                        if not already_added_publications:
                            request_data = requests.get(f"https://doi.org/{clean_publication['doi']}", headers={
                                "Accept": "application/vnd.citationstyles.csl+json"})
                            doi_parser = DOIParser()
                            parsed_json = doi_parser.parse(request_data.json())
                            new_publication = publication_creator.create(parsed_json)

                        else:
                            new_publication = already_added_publications[0]

                if new_publication:
                    new_publication.save()


                for selected_publication_list in selected_publication_lists:
                    target_list = get_object_or_404(PublicationList, id=selected_publication_list)

                    if request.user in target_list.mapping.reviewers.all():
                        if new_publication not in target_list.publications.all():
                            target_list.publications.add(new_publication)
                            target_list.save()

                already_added.append(publication)
                if not query:
                    query = Query(query=query_text, user=request.user, platform=query_platform)
                    query.save()
                query.found_publications.add(new_publication)

        if query:
            query.results = json.dumps(already_added)
            query.save()

        current_list = get_object_or_404(PublicationList, id=int(kwargs["list_id"]))

        return redirect("dashboard_mapping_list",
                        mapping_id=current_list.mapping.id, list_id=current_list.id, permanent=True)

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if request.POST.__contains__("search_on_web"):
            return self.search_on_web(request, *args, **kwargs)

        elif request.POST.__contains__("add_from_web"):
            return self.add_from_web(request, *args, **kwargs)

        else:
            return self.get(request, *args, **kwargs)

