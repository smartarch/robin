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
from django.conf.urls.static import static
from django.conf import settings
from publication.views import AddPublicationByDOI, AddPublicationsByWeb
from .views import PublicView, DashboardView, DashboardAccountView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', PublicView.as_view(), name="public"),
    path('dashboard/', DashboardView.as_view(), name="dashboard"),
    path('dashboard/account', DashboardAccountView.as_view(), name="dashboard_account"),

    # mapping views
    path("dashboard/mapping/", include("mapping.urls")),

    path('publications/add/web/<int:list_id>/', AddPublicationsByWeb.as_view(), name="add_publication_by_web"),
    path('publications/add/doi/', AddPublicationByDOI.as_view(), name="add_publication_by_doi"),

]
if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "interface.views.not_found"
handler500 = "interface.views.server_error"
handler400 = "interface.views.bad_request"
handler403 = "interface.views.access_denied"