from django.urls import path, include

urlpatterns = [
	path("view/", include("publication.model_view_urls")),
	path("edit/", include("publication.model_edit_urls")),
	path("parse/", include("publication.parser_urls")),
]
