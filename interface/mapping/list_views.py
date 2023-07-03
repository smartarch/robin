# typing packages
import re
from typing import Any

from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.core.paginator import Paginator

# local packages
from .models import Mapping, PublicationList, UserPreferences
from .criteria import create_advanced_query

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
		if not request.POST.__contains__("list_created"):
			return redirect("dashboard_mapping_all_lists", permanent=True)

		if "mapping_id" not in kwargs:
			return redirect("dashboard_mapping_all_lists", permanent=True)

		authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
		mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])

		new_publication_list = PublicationList(name=request.POST.get("list_name"), mapping=mapping)
		new_publication_list.save()

		copy_publication_lists(request, authorized_mappings, new_publication_list)

		return redirect("dashboard_mapping_list", mapping_id=mapping.id, list_id=new_publication_list.id, permanent=True)


class MappingListView(LoginRequiredMixin, TemplateView):
	template_name = "mapping/mapping_list.html"

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		if "mapping_id" not in kwargs or "list_id" not in kwargs:
			return redirect("dashboard_mapping_all_lists", permanent=True)

		authorized_mapping = Mapping.objects.filter(reviewers__in=[request.user])
		mapping = get_object_or_404(authorized_mapping, id=kwargs["mapping_id"])
		available_publication_lists = PublicationList.objects.filter(mapping=mapping)
		current_publication_list = get_object_or_404(available_publication_lists, id=kwargs["list_id"])

		copy_instance = user_preference = page_size = None
		move_instead_of_copy = False

		copy_matcher = [re.findall("copy_to_(\d+)",key) for key in request.POST.keys()]
		for copy in copy_matcher:
			if copy:
				copy_id = int(copy[0])
				copy_instance = get_object_or_404(available_publication_lists, id=copy_id)

		move_matcher = [re.findall("move_to_(\d+)", key) for key in request.POST.keys()]
		for move in move_matcher:
			if move:
				move_id = int(move[0])
				move_instead_of_copy = True
				copy_instance = get_object_or_404(available_publication_lists, id=move_id)

		page_sizer = [re.findall("change_page_size_to_(\d+)", key) for key in request.POST.keys()]
		for page in page_sizer:
			if page:
				page_size = int(page[0])
				user_preference = get_object_or_404(UserPreferences, user=request.user)


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
					return redirect("dashboard_mapping_list", mapping_id=mapping.id, list_id=copy_instance.id, permanent=True)

				elif request.POST.__contains__("delete_from_current_list"):
					for pub in available_publications:
						current_publication_list.publications.remove(pub)
						current_publication_list.save()

		if request.POST.__contains__("import_from_publication_lists"):
			publication_lists = [int(x) for x in  request.POST.getlist("selected_lists")]
			authorized_publication_lists = PublicationList.objects.filter(mapping__in=authorized_mapping)
			selected_publication_list_instances = authorized_publication_lists.filter(id__in=publication_lists)

			for selected_publication_list_instance in selected_publication_list_instances:
				for pub in selected_publication_list_instance.publications.all():
					if pub not in current_publication_list.publications.all():
						current_publication_list.publications.add(pub)
						current_publication_list.save()

		if user_preference:
			if page_size is not None:
				user_preference.default_page_size = page_size
				user_preference.save()

		return self.get(request, *args, **kwargs)


	def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Shows the  [current mapping] -> [current -> list] -> Publications
		:param request:
		:param args:
		:param kwargs:
		:return:
		"""
		if "mapping_id" not in kwargs or "list_id" not in kwargs:
			return redirect("dashboard_mapping_all_lists", permanent=True)


		authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
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

		if request.GET.__contains__("filter_text"):
			filter_text = request.GET.get('filter_text')
			if filter_text != "":
				try:
					filter_object = create_advanced_query(filter_text)
					publications = publications.filter(filter_object)
					filter_errors = ""
					filtered_size = len(publications)
				except:
					filter_errors = f"The filter text: {filter_text} has syntax errors. Please double check."

		if request.GET.__contains__("order_text"):
			order_text = request.GET.get("order_text")
		else:
			order_text = "-id"

		publications = publications.order_by(order_text)
		page_size = user_preference.default_page_size if user_preference.default_page_size > 0 else len(publications)
		paginator = Paginator(publications, max(page_size, 25))
		page_number = request.GET.get("page")
		page_obj = paginator.get_page(page_number)

		context = {
			**super().get_context_data(**kwargs),
			"user": request.user,
			"mappings": {mp: PublicationList.objects.filter(mapping=mp) for mp in authorized_mappings},
			"authorized_mappings": authorized_mappings,
			"mapping": mapping,
			"original_size": original_size,
			"filtered_size": filtered_size,
			"filter_text": filter_text,
			"filter_errors": filter_errors,
			"order_text": order_text,
			"available_publication_lists": available_publication_lists,
			"publication_list": publication_list,
			"user_preference": user_preference,
			"available_page_sizes": [x for x in range(25, min(200, original_size), 25)],
			"page_obj": page_obj,
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
			return redirect("dashboard", permanent=True)

		authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
		mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
		available_publication_lists = PublicationList.objects.filter(mapping=mapping)
		if available_publication_lists:
			current_list_id = available_publication_lists[0].id
			return redirect("dashboard_mapping_list", mapping_id=mapping.id, list_id=current_list_id, permanent=True)

		return redirect("dashboard", permanent=True)


class ListDeleteView(LoginRequiredMixin, DeleteView):
	model = PublicationList

	def post(self, request, *args, **kwargs) -> {}:
		if 'mapping_id' not in kwargs or 'list_id' not in kwargs:
			return redirect("dashboard_mapping_all_lists", mapping_id=kwargs["mapping_id"], permanent=True)

		fully_authorized_mappings = Mapping.objects.filter(leader=request.user)
		mapping = get_object_or_404(fully_authorized_mappings, id=kwargs["mapping_id"])
		fully_authorized_lists = PublicationList.objects.filter(mapping=mapping)
		publication_list = get_object_or_404(fully_authorized_lists, id=kwargs["list_id"])

		if request.POST.__contains__("list_deleted"):
			publication_list.delete()

		return redirect("dashboard_mapping_all_lists", mapping_id=kwargs["mapping_id"], permanent=True)