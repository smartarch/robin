from django.urls import path
from . import parser_views

urlpatterns = [
	# details
	path("doi/", parser_views.ParseDOIView.as_view(), name="parse_doi"),
	path("bib/", parser_views.ParseBibView.as_view(), name="parse_bib"),
]