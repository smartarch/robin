from django.urls import path
from .views import AddPublicationByDOI, AddPublicationByBIB

urlpatterns = [
	path('publications/add/web/<int:list_id>/', AddPublicationByDOI.as_view(), name="add_publication_by_web"),
	path('publications/add/doi/', AddPublicationByDOI.as_view(), name="add_publication_by_doi"),
	path('publications/add/bib/', AddPublicationByBIB.as_view(), name="add_publication_by_bib_text"),
]