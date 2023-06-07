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
from publication.views import  HomeView, PublicationView, AddSinglePublication
from .views import PublicView, DashboardView, DashboardAccountView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', PublicView.as_view(), name="public"),
    path('dashboard', DashboardView.as_view(), name="dashboard"),
    path('dashboard/account', DashboardAccountView.as_view(), name="dashboard_account"),
    path('publications/<slug:pk>/', PublicationView.as_view(), name="publications"),
    path('publications/add', AddSinglePublication.as_view(), name="add_single_publication"),
]
