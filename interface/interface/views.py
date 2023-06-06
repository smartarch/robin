from django.views.generic import TemplateView


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
		if request.user:
			context['user'] = request.user
		return self.render_to_response(context)