# typing packages
from typing import Any

# django packages
from django.views.generic import TemplateView, CreateView, View, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
# local packages
from .models import Mapping, PublicationList, UserPreferences
# external packages
import cryptocode
from django.db.models import Q

class CreateUserPreference:

	def find_user_preference (self, user: User, mapping: Mapping, publication_list: PublicationList) -> UserPreferences:
		"""
		Finds the selected user default mapping and default publication list. If it deos not exit, it creates them.
		:param user: Django default user instance which is current request.user (user which is logged in)
		:param mapping:  An instance of mapping model; will be the default the mapping of the user.
		:param publication_list: An instance of current (default) publication list.
		:return: an instance of user preferences which has default mapping and default publication list
		"""
		user_preferences = UserPreferences.objects.filter(user=user)
		if len(user_preferences) == 0:
			user_preference = UserPreferences(user=user)
			user_preference.default_mapping = mapping
			user_preference.default_list = publication_list
			user_preference.save()
		else:
			user_preference = user_preferences[0]
			if not user_preference.default_mapping and mapping and publication_list:
				user_preference.default_mapping = mapping
				user_preference.default_list = publication_list
				user_preference.save()

		return user_preference


class AllMappingsView(LoginRequiredMixin, TemplateView ):
	template_name = "mapping/all.html"

	def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		context = super().get_context_data(**kwargs)

		mappings = Mapping.objects.filter(reviewers__in=[request.user])

		if len(mappings) == 0:
			return redirect("dashboard", permanent=True)

		user_preference = UserPreferences.objects.filter(user=request.user)
		if not user_preference:
			user_preference = UserPreferences(user=request.user)
			user_preference.save()
		else:
			user_preference = user_preference[0]

		context = {
			**context,
			"mappings": mappings,
			"publication_lists": {mapping.id: PublicationList.objects.filter(mapping=mapping) for mapping in mappings},
			"user_preference": user_preference,
		}

		return self.render_to_response(context)

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		if request.POST.__contains__("made_default"):
			user_preference = get_object_or_404(UserPreferences, user=request.user)

			if request.POST.__contains__("mapping_id"):
				user_preference.default_mapping = get_object_or_404(Mapping, id=request.POST.get("mapping_id"))

			if request.POST.__contains__("list_id"):
				user_preference.default_list = get_object_or_404(PublicationList, id=request.POST.get("list_id"))
			user_preference.save()

		return redirect("dashboard_all_mappings", permanent=True)

class NewMappingView(LoginRequiredMixin, TemplateView, CreateUserPreference):
	template_name = "dashboard/index.html"

	def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		context = super().get_context_data(**kwargs)
		context["user"] = request.user
		return self.render_to_response(context)

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Creates a new mapping using the form that is passed
		:param request: the current active request sent by a method=POST
		:param args:
		:param kwargs:
		:return: redirects to either newly created mapping or to the dashboard page.
		"""
		if request.POST.__contains__("mapping_created"):
			new_mapping = Mapping(name=request.POST.get("mapping_name"))

			if request.POST.__contains__("mapping_description"):
				new_mapping.description = request.POST.get("mapping_description")

			new_mapping.leader = request.user
			new_mapping.save()

			new_mapping.reviewers.add(request.user)
			new_mapping.secret_key = cryptocode.encrypt(str(new_mapping.id), "mapping_id_this_is_for_encryption")
			new_mapping.save()

			new_publication_list = PublicationList(name="default", mapping=new_mapping)
			new_publication_list.save()

			_ = self.find_user_preference(request.user, new_mapping, new_publication_list)
			return redirect("dashboard_mapping", mapping_id=new_mapping.id, permanent=True)

		return redirect("dashboard_all_mappings", permanent=True)


class JoinMappingView(LoginRequiredMixin, TemplateView, CreateUserPreference):
	template_name = "dashboard/index.html"

	def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		context = super().get_context_data(**kwargs)
		context["user"] = request.user
		return self.render_to_response(context)

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Join an already created mapping
		:param request: the current active request sent by a method=POST:
		:param args:
		:param kwargs:
		:return: redirects to either newly joined mapping or to the dashboard page.
		"""
		if request.POST.__contains__("mapping_joined"):
			secret_key = request.POST.get("mapping_secret_key")

			mapping_id = int(cryptocode.decrypt(str(secret_key), "mapping_id_this_is_for_encryption"))

			mapping = get_object_or_404(Mapping, id=mapping_id)
			if request.user not in mapping.reviewers.all():
				mapping.reviewers.add(request.user)
				mapping.save()

			publication_list = PublicationList.objects.filter(mapping=mapping)[0]

			user_preference = self.find_user_preference(request.user, mapping, publication_list)
			if not user_preference.default_mapping:
				user_preference.default_mapping = mapping
				user_preference.default_list = publication_list
				user_preference.save()

			return redirect("dashboard_mapping", mapping_id=mapping.id, permanent=True)

		return redirect("dashboard", permanent=True)


class MappingView(LoginRequiredMixin, TemplateView):
	template_name = "mapping/single.html"

	def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Shows the current mapping of the user with mapping_id
		:param request: request: the current active request sent by a GET request
		:param args:
		:param kwargs:
		:return:
		"""
		context = super().get_context_data(**kwargs)
		if 'mapping_id' not in kwargs:
			return redirect("dashboard_all_mappings", permanent=True)

		authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
		mapping = get_object_or_404(authorized_mappings, id=kwargs['mapping_id'])
		current_publication_lists = PublicationList.objects.filter(mapping=mapping)

		publication_list = current_publication_lists[0]

		context['publication_list'] = publication_list
		context['mapping'] = mapping
		context['user'] = request.user
		context['is_leader'] = mapping.leader == request.user

		return self.render_to_response(context)

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		# TODO finish this method
		"""

		:param request:
		:param args:
		:param kwargs:
		:return:
		"""
		context = super().get_context_data(**kwargs)
		if 'mapping' not in kwargs:
			return redirect("dashboard_all_mappings", permanent=True)

		mapping = get_object_or_404(Mapping, id=kwargs['id'])
		context['mapping'] = mapping
		return self.render_to_response(context)


class MappingDeleteView(LoginRequiredMixin, DeleteView):
	model = Mapping

	def post(self, request, *args, **kwargs) -> {}:
		if 'mapping_id' not in kwargs:
			return redirect("dashboard_all_mappings", permanent=True)

		fully_authorized_mappings = Mapping.objects.filter(leader=request.user)
		mapping = get_object_or_404(fully_authorized_mappings, id=kwargs["mapping_id"])

		if request.POST.__contains__("mapping_deleted"):
			mapping.delete()

		return redirect("dashboard_all_mappings", permanent=True)