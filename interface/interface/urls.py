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
from publication.views import AddPublicationByDOI
from review.views import NewReviewView, JoinReviewView, AllReviewsView, ReviewView, ReviewDeleteView
from review.list_views import NewListView, CopyListView, ReviewAllListView, ReviewListView, ListDeleteView
from .views import PublicView, DashboardView, DashboardAccountView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', PublicView.as_view(), name="public"),
    path('dashboard', DashboardView.as_view(), name="dashboard"),
    path('dashboard/account', DashboardAccountView.as_view(), name="dashboard_account"),

    # review views
    path('dashboard/all_reviews', AllReviewsView.as_view(), name="dashboard_all_reviews"),
    path('dashboard/new_review', NewReviewView.as_view(), name="dashboard_review_new"),
    path('dashboard/join_review', JoinReviewView.as_view(), name="dashboard_review_join"),
    path('dashboard/view_review/<int:review_id>/', ReviewView.as_view(), name="dashboard_review"),
    path('dashboard/delete_review/<int:review_id>/', ReviewDeleteView.as_view(), name="dashboard_review_delete"),

    path('dashboard/review/<int:review_id>/all_lists', ReviewAllListView.as_view(), name="dashboard_review_all_lists"),
    path('dashboard/review/<int:review_id>/new_list', NewListView.as_view(), name="dashboard_review_new_list"),
    path('dashboard/review/<int:review_id>/copy_to_list/<int:list_id>/', CopyListView.as_view(),
         name="dashboard_review_copy_list"),
    path('dashboard/review/<int:review_id>/view_list/<int:list_id>/', ReviewListView.as_view(),
         name="dashboard_review_list"),
    path('dashboard/review/<int:review_id>/delete_list/<int:list_id>/', ListDeleteView.as_view(),
         name="dashboard_review_list_delete"),


    path('publications/add/doi', AddPublicationByDOI.as_view(), name="add_publication_by_doi"),
]
