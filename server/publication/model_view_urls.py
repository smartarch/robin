from django.urls import path
from . import model_views

urlpatterns = [
	# lists
	path("sources",	model_views.SerializedSourceView.as_view(),	name="list_sources"),
	path("countries", model_views.SerializedCountryView.as_view(), name="list_countries"),
	path("affiliations", model_views.SerializedAffiliationView.as_view(), name="list_affiliations"),
	path("authors",	model_views.SerializedAuthorView.as_view(),	name="list_authors"),
	path("venues", model_views.SerializedVenueView.as_view(), name="list_venues"),
	path("keywords", model_views.SerializedKeywordView.as_view(), name="list_keywords"),
	path("publications", model_views.SerializedPublicationView.as_view(), name="list_publications"),
	path("full-texts", model_views.SerializedFullTextView.as_view(), name="list_full-texts"),

	# details
	path("source/<int:pk>/", model_views.SerializedSourceView.as_view(), name="retrieve_source_detail"),
	path("country/<int:pk>/", model_views.SerializedCountryView.as_view(), name="retrieve_country_detail"),
	path("affiliation/<int:pk>/", model_views.SerializedAffiliationView.as_view(), name="retrieve_affiliation_detail"),
	path("author/<int:pk>/", model_views.SerializedAuthorView.as_view(), name="retrieve_author_detail"),
	path("venue/<int:pk>/", model_views.SerializedVenueView.as_view(), name="retrieve_venue_detail"),
	path("keyword/<int:pk>/", model_views.SerializedKeywordView.as_view(), name="retrieve_keyword_detail"),
	path("publication/<int:pk>/", model_views.SerializedPublicationView.as_view(), name="retrieve_publication_detail"),
	path("full-text/<int:pk>/", model_views.SerializedFullTextView.as_view(), name="retrieve_full-text_detail"),
]
