from typing import Any

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
from mapping.models import PublicationList
from django.shortcuts import get_object_or_404, redirect
# parsers
from .parsers import parse_doi
from .factories import PublicationFactory


class AddPublicationByDOI(LoginRequiredMixin, CreateView):
    mode = Publication

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
            parsed_json = parse_doi(request_data.json())

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