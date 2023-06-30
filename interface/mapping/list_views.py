# typing packages
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


class CopyListView(LoginRequiredMixin, UpdateView):

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Creates a new publication list
		:param request:
		:param args:
		:param kwargs:
		:return:
		"""
		if not request.POST.__contains__("list_copied"):
			return redirect("dashboard_mapping_all_lists", permanent=True)

		if "mapping_id" not in kwargs:
			return redirect("dashboard_mapping_all_lists", permanent=True)

		authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
		mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])

		available_publication_lists = PublicationList.objects.filter(mapping=mapping)
		publication_list = get_object_or_404(available_publication_lists, id=kwargs['list_id'])

		copy_publication_lists(request, authorized_mappings, publication_list)

		return redirect("dashboard_mapping_list", mapping_id=mapping.id, list_id=publication_list.id, permanent=True)


class MappingListView(LoginRequiredMixin, TemplateView):
	template_name = "mapping/mapping_list.html"

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

		authorized_mapping = Mapping.objects.filter(reviewers__in=[request.user])
		mapping = get_object_or_404(authorized_mapping, id=kwargs["mapping_id"])
		available_publication_lists = PublicationList.objects.filter(mapping=mapping)
		publication_list = get_object_or_404(available_publication_lists, id=kwargs['list_id'])
		user_preference = get_object_or_404(UserPreferences, user=request.user)

		# for paging (for example 25 publications per page)
		publications = publication_list.publications.all()

		if request.GET.__contains__("filter_text"):
			filter_text = request.GET.get('filter_text')
			try:
				filter_object = create_advanced_query(filter_text)
				publications = publications.filter(publications)
				filter_errors = ""
			except BufferError:
				filter_errors = f"The filter text: {filter_text} has syntax errors. Please double check."
		else:
			filter_text = ""
			filter_errors = ""

		if request.GET.__contains__("order_text"):
			order_text = request.GET.get("order_text")
		else:
			order_text = "-id"

		publications = publications.order_by(order_text)

		paginator = Paginator(publications, user_preference.default_page_size)
		page_number = request.GET.get("page")
		page_obj = paginator.get_page(page_number)

		context = {
			**super().get_context_data(**kwargs),
			"user": request.user,
			"authorized_mappings": authorized_mapping,
			"mapping": mapping,
			"filter_text": filter_text,
			"filter_errors": filter_errors,
			"order_text": order_text,
			"available_publication_lists": available_publication_lists,
			"publication_list": publication_list,
			"user_preference": user_preference,
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