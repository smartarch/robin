# typing packages
import csv
import os
import re
from typing import Any

import requests
from django.core.exceptions import FieldError
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from pypdf import PdfReader
from pypdf.errors import PdfReadError

# local packages
from .models import Mapping, PublicationList, UserPreferences, ReviewField, ReviewFieldValue, ReviewFieldValueCoding
from .criteria import create_advanced_query
from .field_views import FieldReviewView

# from external packages
from publication.models import FullText, FullTextAccess, Publication

from django.conf import settings


def copy_publication_lists(request: Any, authorized_mappings: Any, publication_list: Any) -> None:
    if request.POST.__contains__("copy_from"):
        copy_from = [int(x) for x in request.POST.get_list("copy_from")]
        authorized_publication_lists = PublicationList.objects.filter(mapping__in=authorized_mappings)
        clones = authorized_publication_lists.filter(id__in=copy_from)
        for clone in clones:
            for publication in clone.publications:
                if publication not in publication_list.publications.all():
                    publication_list.publications.add(publication)

        publication_list.save()


class NewListView(LoginRequiredMixin, CreateView):

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Creates a new publication list
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        if "mapping_id" not in kwargs:
            return redirect("mapping_all")

        if not request.POST.__contains__("list_created"):
            return redirect("publication_list_all", mapping_id=kwargs["mapping_id"])

        user = request.user

        authorized_mappings = Mapping.objects.filter(reviewers__in=[user])
        mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])

        new_publication_list = PublicationList(name=request.POST.get("list_name"), mapping=mapping, reviewer=user)
        new_publication_list.save()

        copy_publication_lists(request, authorized_mappings, new_publication_list)

        return redirect("publication_list", mapping_id=mapping.id, list_id=new_publication_list.id)


class MappingListView(LoginRequiredMixin, TemplateView):
    template_name = "mapping/mapping_list.html"

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if "mapping_id" not in kwargs or "list_id" not in kwargs:
            return redirect("mapping_all")

        authorized_mapping = Mapping.objects.filter(reviewers__in=[request.user])
        mapping = get_object_or_404(authorized_mapping, id=kwargs["mapping_id"])
        available_publication_lists = PublicationList.objects.filter(mapping=mapping)
        current_publication_list = get_object_or_404(available_publication_lists, id=kwargs["list_id"])
        user = request.user

        copy_instance = user_preference = page_size = subscriber_instance_end = follower_instance = None
        move_instead_of_copy = False

        copy_move_new = [re.findall("(move|copy)_to_new_list", key) for key in request.POST.keys()]
        for copy_move in copy_move_new:
            if copy_move:
                new_list_name = request.POST.get(f"new_list_name_{copy_move[0]}")
                new_publication_list = PublicationList(name=new_list_name, mapping=mapping, reviewer=user)
                new_publication_list.save()

                copy_instance = new_publication_list
                move_instead_of_copy = copy_move[0] == "move"

        copy_matcher = [re.findall(r"copy_to_(\d+)", key) for key in request.POST.keys()]

        for copy in copy_matcher:
            if copy:
                copy_id = int(copy[0])
                copy_instance = get_object_or_404(available_publication_lists, id=copy_id)

        move_matcher = [re.findall(r"move_to_(\d+)", key) for key in request.POST.keys()]
        for move in move_matcher:
            if move:
                move_id = int(move[0])
                move_instead_of_copy = True
                copy_instance = get_object_or_404(available_publication_lists, id=move_id)

        page_sizer = [re.findall(r"change_page_size_to_(\d+)", key) for key in request.POST.keys()]
        for page in page_sizer:
            if page:
                page_size = int(page[0])
                user_preference = get_object_or_404(UserPreferences, user=user)

        subscription_ender = [re.findall(r"end_subscription_(\d+)", key) for key in request.POST.keys()]
        for subscriber in subscription_ender:
            if subscriber:
                subscriber_id = int(subscriber[0])
                subscriber_instance_end = get_object_or_404(PublicationList, id=subscriber_id)

        followers = [re.findall(r"follow_(\d+)", key) for key in request.POST.keys()]
        for follower in followers:
            if follower:
                follower_id = int(follower[0])
                follower_instance = get_object_or_404(PublicationList, id=follower_id)

        selected_publications = [int(x) for x in request.POST.getlist("selected_publications")]
        if selected_publications:
            available_publications = current_publication_list.publications.filter(id__in=selected_publications)
            if available_publications:
                if copy_instance:
                    for pub in available_publications:
                        if pub not in copy_instance.publications.all():
                            copy_instance.publications.add(pub)
                            copy_instance.save()
                        if move_instead_of_copy:
                            current_publication_list.publications.remove(pub)
                            current_publication_list.save()
                    return redirect("publication_list", mapping_id=mapping.id, list_id=copy_instance.id)

                elif request.POST.__contains__("delete_from_current_list"):
                    for pub in available_publications:
                        current_publication_list.publications.remove(pub)
                        current_publication_list.save()

        if request.POST.__contains__("import_from_publication_lists"):
            publication_lists = [int(x) for x in request.POST.getlist("selected_lists")]
            authorized_publication_lists = PublicationList.objects.filter(mapping__in=authorized_mapping)
            selected_publication_list_instances = authorized_publication_lists.filter(id__in=publication_lists)

            for selected_publication_list_instance in selected_publication_list_instances:
                for pub in selected_publication_list_instance.publications.all():
                    if pub not in current_publication_list.publications.all():
                        current_publication_list.publications.add(pub)
                        current_publication_list.save()

        if request.POST.__contains__("export_as_csv"):
            selected_publications = request.POST.getlist("selected_publications")
            user_fields = ReviewField.objects.filter(mapping=mapping)
            reviewers = mapping.reviewers.all()
            print (reviewers)
            csv_columns = ['id', 'title', 'doi', 'year', 'venue', 'publisher', 'publication_list']
            for reviewer in reviewers:
                for user_field in user_fields:
                    csv_columns.append(f"{reviewer.initials()}:{user_field.name}")

            fn = settings.MEDIA_ROOT / f"temp/robin_list_{current_publication_list.name}_{request.user.id}.csv"
            with open(fn, "w") as csv_file:
                csv_file.write(','.join(csv_columns) + "\n")
                for selected_publication in selected_publications:
                    selected_publication_object = get_object_or_404(Publication, id=selected_publication)
                    data = [
                            str(selected_publication_object.id),
                            str(selected_publication_object.title.replace(',', ';')),
                            str(selected_publication_object.doi),
                            str(selected_publication_object.year),
                            str(selected_publication_object.venue.name.replace(',', ';')),
                            str(selected_publication_object.venue.publisher.replace(',', ';')),
                            str(current_publication_list.name)
                    ]
                    for reviewer in reviewers:
                        for user_field in user_fields:
                            field_value = ReviewFieldValue.get_value(user_field, selected_publication_object, reviewer)
                            if field_value is None:
                                data.append("not set")
                            else:
                                data.append(str(field_value).replace(',', ';'))
                    csv_file.write(','.join(data) + "\n")

            with open(fn, "r") as csv_file:
                response = HttpResponse(csv_file.read(), content_type="text/csv")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(fn)
                return response

        if user_preference:
            if page_size is not None:
                user_preference.default_page_size = page_size
                user_preference.save()

        if subscriber_instance_end:
            current_publication_list.subscriptions.remove(subscriber_instance_end)
            current_publication_list.save(auto_update=True)
            subscriber_instance_end.followers.remove(current_publication_list)
            subscriber_instance_end.save()

        if follower_instance:
            if follower_instance not in current_publication_list.followers.all():
                current_publication_list.subscriptions.add(follower_instance)
                current_publication_list.save()
                follower_instance.followers.add(current_publication_list)
                follower_instance.save()

        if request.POST.__contains__("create_view"):
            new_view_name = request.POST.get("view_name")
            filtered_text = request.POST.get("filtered_text")
            new_view = PublicationList(name=new_view_name, mapping=mapping, criteria=filtered_text, reviewer=user)
            new_view.save()
            new_view.type = "Automated"
            new_view.subscriptions.add(current_publication_list)
            new_view.save()
            current_publication_list.followers.add(new_view)
            current_publication_list.save()
            return redirect("publication_list", mapping_id=mapping.id, list_id=new_view.id)

        return self.get(request, *args, **kwargs)

    def compare(self, publication_list: PublicationList, publications: Any, filter_object: Any = None) -> {}:
        found = [pub for pub in publications if pub in publication_list.publications.all()]
        compact_results = {
            'shared': len(found),
            'shared_rate': f"{100 * len(found) / len(publications):0.2f}%" if len(publications) > 0 else "",
            'total': len(publications),
        }
        if not filter_object:
            return compact_results
        else:
            only_in_results = [pub for pub in publications if pub not in publication_list.publications.all()]
            only_in_list = [pub for pub in publication_list.publications.all() if pub not in publications]
            return {
                **compact_results,
                "found": found,
                "only_in_results": only_in_results,
                "only_in_list": only_in_list,
            }

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Shows the  [current mapping] -> [current -> list] -> Publications
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if "mapping_id" not in kwargs or "list_id" not in kwargs:
            return redirect("mapping_all")

        authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])

        if len(authorized_mappings) == 0:
            return redirect("publication_list_all", mapping_id=kwargs["mapping_id"])

        mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
        available_publication_lists = PublicationList.objects.filter(mapping=mapping)
        publication_list = get_object_or_404(available_publication_lists, id=kwargs['list_id'])
        user_preference = get_object_or_404(UserPreferences, user=request.user)

        # for paging (for example 25 publications per page)
        publications = publication_list.publications.all()
        original_size = len(publications)

        filter_text = ""
        filter_errors = ""
        filtered_size = None

        compared = {}
        detailed_results = {}
        overall_results = {
            'all': {
                pub_list.id: self.compare(pub_list, publications)
                for pub_list in available_publication_lists
            }
        }

        if request.GET.__contains__("filter_text"):
            filter_text = request.GET.get('filter_text')
            if filter_text != "":
                try:
                    filter_object = create_advanced_query(mapping, publication_list,filter_text)
                    publications = publications.filter(filter_object)
                    filter_errors = ""
                    filtered_size = len(publications)
                    overall_results['filtered'] = {
                        pub_list.id: self.compare(pub_list, publications)
                        for pub_list in available_publication_lists
                    }
                    if request.GET.__contains__("compare_to"):
                        compared = {
                            int(x): get_object_or_404(available_publication_lists, id=int(x))
                            for x in request.GET.getlist("compare_to")
                        }
                        detailed_results = {
                            publication_list: self.compare(publication_list, publications, filter_object)
                            for _, publication_list in compared.items()
                        }
                except FieldError as e:
                    filter_errors = str(e)
                    filter_text = None

                except BufferError:
                    filter_errors = "please check syntax of the filter"
                    filter_text = None

        if request.GET.__contains__("order_text"):
            order_text = request.GET.get("order_text")
        else:
            order_text = "-id"

        publications = publications.order_by(order_text)
        page_size = user_preference.default_page_size if user_preference.default_page_size > 0 else len(publications)
        paginator = Paginator(publications, max(page_size, 25))
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        review_fields = ReviewField.objects.filter(mapping=mapping)
        coding_codes = {
            field: ReviewFieldValueCoding.get_all_codes(field)
            for field in review_fields if field.type == "C"
        }

        # full access only PDF for now
        full_accesses = FullTextAccess.objects.filter(mapping=mapping).filter(full_text__type="P")
        # check for failed downloads
        user_errors = ""
        for full_access in full_accesses:

            if full_access.status == "N":
                user_errors += f"Cannot download {full_access.full_text.publication.title}, access denied, try to upload manually.\n"
                if full_access.file is not None:
                    full_access.status = "U"
                else:
                    full_access.status = "E"
                full_access.save()
        # in case we do not have one item at least, the `get` should be changed to `filter`
        publication_full_texts = {}
        for publication in page_obj:
            full_accesses_per_publication = full_accesses.filter(full_text__publication=publication.id)
            if len(full_accesses_per_publication) == 0:
                publication_full_texts[publication] = None
            else:
                publication_full_texts [publication] = full_accesses_per_publication[0]

        context = {
            **super().get_context_data(**kwargs),
            "user": request.user,
            "mappings": {mp: PublicationList.objects.filter(mapping=mp) for mp in authorized_mappings},
            "authorized_mappings": authorized_mappings,
            "mapping": mapping,
            "compared": compared.keys(),
            "overall_results": overall_results,
            "detailed_results": detailed_results,
            "original_size": original_size,
            "review_fields": review_fields,
            "coding_codes": coding_codes,
            "filtered_size": filtered_size,
            "filter_text": filter_text,
            "filter_errors": filter_errors,
            "order_text": order_text,
            "available_publication_lists": available_publication_lists,
            "publication_list": publication_list,
            "user_preference": user_preference,
            "available_page_sizes": [x for x in range(25, min(201, original_size + 1), 25)],
            "publication_full_texts": publication_full_texts,
            "page_obj": page_obj,
            "user_errors": user_errors if user_errors else None,
        }

        return self.render_to_response(context)


class MappingAllListView(LoginRequiredMixin, View):

    def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Shows the  [current mapping] -> [first -> list] -> Publications
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if "mapping_id" not in kwargs:
            return redirect("dashboard")

        authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
        mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
        available_publication_lists = PublicationList.objects.filter(mapping=mapping)
        if available_publication_lists:
            current_list_id = available_publication_lists[0].id
            return redirect("publication_list", mapping_id=mapping.id, list_id=current_list_id)

        return redirect("dashboard")


class ListDeleteView(LoginRequiredMixin, DeleteView):
    model = PublicationList

    def post(self, request, *args, **kwargs) -> {}:
        if 'mapping_id' not in kwargs or 'list_id' not in kwargs:
            return redirect("publication_list_all", mapping_id=kwargs["mapping_id"])

        fully_authorized_mappings = Mapping.objects.filter(leader=request.user)
        mapping = get_object_or_404(fully_authorized_mappings, id=kwargs["mapping_id"])
        fully_authorized_lists = PublicationList.objects.filter(mapping=mapping)
        publication_list = get_object_or_404(fully_authorized_lists, id=kwargs["list_id"])

        if request.POST.__contains__("list_deleted"):
            if len(fully_authorized_lists) > 1:
                publication_list.delete()

        return redirect("publication_list_all", mapping_id=kwargs["mapping_id"])


class GetAccessForListView(LoginRequiredMixin, View):
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if "mapping_id" not in kwargs or "list_id" not in kwargs:
            return redirect("mapping_all")

        authorized_mapping = Mapping.objects.filter(reviewers__in=[request.user])
        mapping = get_object_or_404(authorized_mapping, id=kwargs["mapping_id"])

        if "fullTextAccessID" in request.POST:
            full_text_access_id = request.POST.get("fullTextAccessID")
            full_text_access = get_object_or_404(FullTextAccess, id=full_text_access_id)

            if "get_full_text_access" in request.POST:
                full_text = full_text_access.full_text
                if full_text.url != "":
                    resource_request = requests.get(full_text.url, headers={
                        "Accept": "text/html,application/xhtml+xml,application/pdf,application/xml;q=0.9,image/avif,image/webp",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"})

                    if resource_request.status_code == 200:
                        filename = f"full_text/m-{mapping.__hash__()}/" \
                                   + f"p-{full_text_access.full_text.publication.__hash__()}.pdf"
                        os.makedirs(settings.BASE_DIR / f"media/full_text/m-{mapping.__hash__()}/", exist_ok=True)

                        file_path = settings.BASE_DIR / f"media/{filename}"
                        with open(file_path, "wb") as resource_file:
                            resource_file.write(resource_request.content)

                            if full_text.type == "P":
                                try:
                                    PdfReader(file_path)
                                    full_text_access.file.name = str(filename)
                                    full_text_access.status = "D"
                                    full_text_access.save()

                                except:
                                    try:
                                        os.remove(file_path)
                                    except:
                                        pass


            elif "upload_file_text_access" in request.POST:
                full_text_access_id = request.POST.get("fullTextAccessID")
                uploaded_file = request.FILES['uploaded_file']
                fs = FileSystemStorage()
                filename = f"full_text/m-{mapping.__hash__()}/" \
                           + f"p-{full_text_access.full_text.publication.__hash__()}.pdf"
                os.makedirs(settings.BASE_DIR / f"media/full_text/m-{mapping.__hash__()}/", exist_ok=True)

                try:
                    os.remove(settings.BASE_DIR / f"media/{filename}")
                except:
                    pass

                filename = fs.save(filename, uploaded_file)
                full_text_access = get_object_or_404(FullTextAccess, id=full_text_access_id)
                full_text_access.status = "U"

                full_text_access.file = filename
                full_text_access.save()

            elif "delete_full_text_access" in request.POST:
                full_text_access_id = request.POST.get("fullTextAccessID")
                full_text_access = get_object_or_404(FullTextAccess, id=full_text_access_id)
                try:
                    os.remove(settings.BASE_DIR / f"media/{full_text_access.file}")
                except:
                    pass
                if full_text_access.status == "D":
                    previous_filename = f"full_text/m-{mapping.__hash__()}/" \
                               + f"p-{full_text_access.full_text.publication.__hash__()}.pdf"

                    if (settings.BASE_DIR / f"media/{previous_filename}").exists():
                        full_text_access.status = "U"
                        full_text_access.file = previous_filename
                    else:
                        full_text_access.status = "E"
                        full_text_access.file = ""
                elif full_text_access.status == "U":
                    previous_filename = f"full_text/m-{mapping.__hash__()}/" \
                                        + f"p-{full_text_access.full_text.publication.__hash__()}_original.pdf"
                    if (settings.BASE_DIR / f"media/{previous_filename}").exists():
                        full_text_access.status = "D"
                        full_text_access.file = previous_filename
                    else:
                        full_text_access.status = "E"
                        full_text_access.file = ""
                else:
                    full_text_access.status = "E"
                    full_text_access.file = ""
                full_text_access.save()

        return redirect("publication_list", mapping_id=kwargs["mapping_id"], list_id=kwargs["list_id"])
