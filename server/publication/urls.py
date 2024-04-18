from django.urls import path, include

urlpatterns = [
	path("view/", include("publication.view_urls")),
	# path("insert/", include("publication.insert_urls")),
	# path("update/", include("publication.update_urls")),
	# path("delete/", include("publication.delete_urls"))
]
