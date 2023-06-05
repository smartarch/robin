from django.http import HttpResponse
from django.core.paginator import Paginator
from django.template import loader
from django.db.models import Q
from django.views.generic import TemplateView, View
from .models import Publication, Keywords
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
import requests

# parsers
from .parsers import parse_cross_ref_json
from .factories import PublicationFactory


class HomeView (TemplateView):
    template_name = "publications/index.html"

    def get(self, request, *args, **kwargs) -> {}:
        context = super().get_context_data(**kwargs)
        publications = Publication.objects.all()
        year_from = request.GET.get("year_from")
        year_to = request.GET.get("year_to")
        sources = request.GET.get("sources")
        search = request.GET.get("search")
        order_by = request.GET.get("order_by")
        search_text = []

        if len(publications) == 0:
            return self.render_to_response(context)

        if year_from:
            publications = publications.filter(year__gte=year_from)
            search_text.append(f"year_from={year_from}")
        else:
            year_from = min(publications.order_by().values_list('year').distinct())[0]

        if year_to:
            publications = publications.filter(year__lte=year_to)
            search_text.append(f"year_to={year_to}")
        else:
            year_to = max(publications.order_by().values_list('year').distinct())[0]

        if search:
            terms = [x.strip('\"') for x in search.split(',')]
            for term in terms:
                all_keys = Keywords.objects.filter(name__icontains=term.lower())
                publications = publications.filter(Q(title__icontains=term.lower()) | Q(abstract__icontains=term.lower())\
                        | Q(author_keywords__in=all_keys) | Q(index_keywords__in=all_keys)).distinct()

            if len(terms) > 0:
                search_text.append(f"search=\"{(','.join(terms))}\"")
        else:
            terms = []

        distinct_sources = {x[0]: len(publications.filter(source=x[0]))
                            for x in publications.order_by().values_list('source').distinct()}
        if sources:
            if not sources == "all":
                source_names = [x.strip('\"') for x in sources.split(',')]
                publications = publications.filter(source__in=source_names)
            search_text.append(f"sources={sources}")

        if order_by:
            publications = publications.order_by(order_by.strip("\""))
            search_text.append(f"order_by={order_by}")

        paginator = Paginator(publications, 25)  # Show 25 contacts per page.
        page_number = request.GET.get("page")

        page_obj = paginator.get_page(page_number)
        prev_pages = [page_obj.number - i
                      for i in range(5, 0, -1)
                      if page_obj.number - i > 0]
        next_pages = [page_obj.number + i
                      for i in range(1, 6)
                      if page_obj.number + i <= paginator.num_pages]

        context = {
            **context,
            "page_obj": page_obj,
            "prev_pages": prev_pages,
            "next_pages": next_pages,
            "year_from": year_from,
            "year_to": year_to,
            "terms": terms,
            "size": len(publications),
            "sources": [x.strip("\"") for x in sources.split(',')] if sources else "all",
            "distinct_sources": distinct_sources,
            "search_text": ('&' if len(search_text) > 0 else "") + '&'.join(search_text),
        }
        return self.render_to_response(context)


class AddSinglePublication (LoginRequiredMixin, View):
    template_name = "publications/index.html"

    def post(self, request, *args, **kwargs) -> {}:
        doi = request.POST.get("doi")

        request_data = requests.get(f"https://api.crossref.org/works/{doi}")
        parsed_json = parse_cross_ref_json(request_data.json())

        publication_creator = PublicationFactory()
        new_publication = publication_creator.create(parsed_json)
        if new_publication:
            new_publication.user = request.user
            new_publication.save()
        request.method = "GET"
        return HomeView.as_view()(request)



class PublicationView (LoginRequiredMixin, TemplateView):
    template_name = "publications/single.html"

    def get(self, request, *args, **kwargs) -> {}:
        context = super().get_context_data(**kwargs)
        # Search for given publication, if not found, send an empty context
        if "pk" in kwargs:
            if kwargs["pk"].lower() == "new":
                context["forms"] = {
                }
            else:
                try:
                    context["publication"] = Publication.objects.get(pk=kwargs["pk"])
                except ObjectDoesNotExist:
                    pass

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs) -> {}:
        context = super().get_context_data(**kwargs)


        return self.render_to_response(context)
#
# def publication_view(request):
#     pubs = Publication.objects.all()
#     year_from = request.GET.get("year_from")
#     year_to = request.GET.get("year_to")
#     sources = request.GET.get("sources")
#     search = request.GET.get("search")
#     order_by = request.GET.get("order_by")
#     search_text = []
#
#     if year_from:
#         pubs = pubs.filter(year__gte=year_from)
#         search_text.append(f"year_from={year_from}")
#     else:
#         year_from = min(pubs.order_by().values_list('year').distinct())[0]
#
#     if year_to:
#         pubs = pubs.filter(year__lte=year_to)
#         search_text.append(f"year_to={year_to}")
#     else:
#         year_to = max(pubs.order_by().values_list('year').distinct())[0]
#
#     if search:
#         terms = [x.strip('\"') for x in search.split(',')]
#         for term in terms:
#             all_keys = Keywords.objects.filter(name__icontains=term.lower())
#             pubs = pubs.filter(Q(title__icontains=term.lower()) \
#                                | Q(abstract__icontains=term.lower()) \
#                                | Q(author_keywords__in=all_keys) \
#                                | Q(index_keywords__in=all_keys)).distinct()
#
#         if len(terms) > 0:
#             search_text.append(f"search=\"{(','.join(terms))}\"")
#     else:
#         terms = []
#
#     distinct_sources = {x[0]: len(pubs.filter(source=x[0]))
#                         for x in pubs.order_by().values_list('source').distinct()}
#     if sources:
#         if not sources == "all":
#             source_names = [x.strip('\"') for x in sources.split(',')]
#             pubs = pubs.filter(source__in=source_names)
#         search_text.append(f"sources={sources}")
#
#     if order_by:
#         pubs = pubs.order_by(order_by.strip("\""))
#         search_text.append(f"order_by={order_by}")
#
#     paginator = Paginator(pubs, 25)  # Show 25 contacts per page.
#     page_number = request.GET.get("page")
#
#     page_obj = paginator.get_page(page_number)
#     prev_pages = [page_obj.number - i
#                   for i in range(5, 0, -1)
#                   if page_obj.number - i > 0]
#     next_pages = [page_obj.number + i
#                   for i in range(1, 6)
#                   if page_obj.number + i <= paginator.num_pages]
#
#     context = {
#         "page_obj": page_obj,
#         "prev_pages": prev_pages,
#         "next_pages": next_pages,
#         "year_from": year_from,
#         "year_to": year_to,
#         "terms": terms,
#         "size": len(pubs),
#         "sources": [x.strip("\"") for x in sources.split(',')] if sources else "all",
#         "distinct_sources": distinct_sources,
#         "search_text": ('&' if len(search_text) > 0 else "") + '&'.join(search_text),
#     }
#
#     template = loader.get_template('publications/index.html')
#     return HttpResponse(template.render(context, request))
#
