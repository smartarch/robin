from django.urls import path
from . import model_edit_views

urlpatterns = [
	# details
	path("source/<int:pk>/", model_edit_views.SerializedSourceEditView.as_view(), name="edit_source"),
	path("country/<int:pk>/", model_edit_views.SerializedCountryEditView.as_view(), name="edit_country"),
	path("affiliation/<int:pk>/", model_edit_views.SerializedAffiliationEditView.as_view(), name="edit_affiliation"),
	path("author/<int:pk>/", model_edit_views.SerializedAuthorEditView.as_view(), name="edit_author"),
	path("venue/<int:pk>/", model_edit_views.SerializedVenueEditView.as_view(), name="edit_venue"),
	path("keyword/<int:pk>/", model_edit_views.SerializedKeywordEditView.as_view(), name="edit_keyword"),
	path("publication/<int:pk>/", model_edit_views.SerializedPublicationEditView.as_view(), name="edit_publication"),
	path("full-text/<int:pk>/", model_edit_views.SerializedFullTextEditView.as_view(), name="edit_full-text"),
]