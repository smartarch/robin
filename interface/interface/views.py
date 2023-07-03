from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from mapping.models import Mapping, UserPreferences
from allauth.socialaccount.models import SocialApp

class PublicView(TemplateView):
	template_name = "public/index.html"

	def get(self, request, *args, **kwargs) -> {}:
		"""
		A class based view for default page in Django

		:param request: request from
		:param args: request arguments
		:param kwargs: request key value arguments
		:return: shall return context which is a dictionary and render using templated name
		"""
		context = super().get_context_data(**kwargs)
		github_enabled = SocialApp.objects.filter(name="github")

		context["github_not_defined"] = len(github_enabled) == 0

		if request.user:
			return redirect("dashboard", permanent=True)
		return self.render_to_response(context)


class DashboardView(LoginRequiredMixin, TemplateView):
	template_name = "dashboard/index.html"

	def get(self, request, *args, **kwargs) -> {}:
		"""
		A class based view for default authorized page in Django

		:param request: request from
		:param args: request arguments
		:param kwargs: request key value arguments
		:return: shall return context which is a dictionary and render using templated name
		"""
		context = super().get_context_data(**kwargs)
		context['user'] = request.user
		mappings = Mapping.objects.filter(reviewers__in=[request.user])
		if len(mappings) > 0:
			context['mappings'] = mappings
			user_preferences = UserPreferences.objects.filter(user=request.user)
			if len(user_preferences) > 0:
				mapping = user_preferences[0].default_mapping
				def_list = user_preferences[0].default_list
				return redirect("dashboard_mapping_list", mapping_id=mapping.id, list_id=def_list.id, permanent=True)

			return redirect("dashboard_all_mappings",  permanent=True)

		return self.render_to_response(context)


class DashboardAccountView(LoginRequiredMixin, TemplateView):
	template_name = "dashboard/account.html"

	def get(self, request, *args, **kwargs) -> {}:
		"""
		A class based view for default authorized page in Django

		:param request: request from
		:param args: request arguments
		:param kwargs: request key value arguments
		:return: shall return context which is a dictionary and render using templated name
		"""
		context = super().get_context_data(**kwargs)
		context['user'] = request.user
		return self.render_to_response(context)

	def post(self, request, *args, **kwargs) -> {}:
		"""
		A class method that sets/changes/ the password  and other information for a user,

		:param request: request from
		:param args: request arguments
		:param kwargs: request key value arguments
		:return: shall return context which is a dictionary and render using templated name
		"""

		if request.POST.__contains__("profile_saved"):
			if request.user.is_active:
				request.user.first_name = request.POST.get("first_name")
				request.user.last_name = request.POST.get("last_name")
				request.user.email = request.POST.get("email")
				request.user.save()

		if request.POST.__contains__("user_deactivated"):
			request.user.is_active = False
			request.user.save()

		context = super().get_context_data(**kwargs)
		context['user'] = request.user
		return self.render_to_response(context)


def not_found(request, exception):
	return render(request, 'errors/404.html', context={"exception": exception})

def server_error(request):
	return render(request, 'errors/500.html')
def bad_request(request, exception):
	return render(request, 'errors/500.html')

def access_denied(request, exception):
	return render(request, 'errors/500.html')