"""
URL configuration for interface project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from publication.views import AddPublicationByDOI, AddPublicationsByBibText, AddPublicationsByWeb
from mapping.views import NewMappingView, JoinMappingView, AllMappingsView, MappingView, MappingDeleteView
from mapping.list_views import NewListView, CopyListView, MappingAllListView, MappingListView, ListDeleteView
from .views import PublicView, DashboardView, DashboardAccountView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', PublicView.as_view(), name="public"),
    path('dashboard', DashboardView.as_view(), name="dashboard"),
    path('dashboard/account', DashboardAccountView.as_view(), name="dashboard_account"),

    # mapping views
    path('dashboard/all_mappings', AllMappingsView.as_view(), name="dashboard_all_mappings"),
    path('dashboard/new_mapping', NewMappingView.as_view(), name="dashboard_mapping_new"),
    path('dashboard/join_mapping', JoinMappingView.as_view(), name="dashboard_mapping_join"),
    path('dashboard/view_mapping/<int:mapping_id>/', MappingView.as_view(), name="dashboard_mapping"),
    path('dashboard/delete_mapping/<int:mapping_id>/', MappingDeleteView.as_view(), name="dashboard_mapping_delete"),

    path('dashboard/mapping/<int:mapping_id>/all_lists', MappingAllListView.as_view(),
         name="dashboard_mapping_all_lists"),
    path('dashboard/mapping/<int:mapping_id>/new_list', NewListView.as_view(), name="dashboard_mapping_new_list"),
    path('dashboard/mapping/<int:mapping_id>/copy_to_list/<int:list_id>/', CopyListView.as_view(),
         name="dashboard_mapping_copy_list"),
    path('dashboard/mapping/<int:mapping_id>/view_list/<int:list_id>/', MappingListView.as_view(),
         name="dashboard_mapping_list"),
    path('dashboard/mapping/<int:mapping_id>/delete_list/<int:list_id>/', ListDeleteView.as_view(),
         name="dashboard_mapping_list_delete"),

    path ('publications/add/bib_text', AddPublicationsByBibText.as_view(), name="add_publication_by_bib_text"),
    path('publications/add/web/<int:list_id>/', AddPublicationsByWeb.as_view(), name="add_publication_by_web"),
    path('publications/add/doi', AddPublicationByDOI.as_view(), name="add_publication_by_doi"),
]
