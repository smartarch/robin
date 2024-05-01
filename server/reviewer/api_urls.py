from django.urls import path
from .views import ReviewerProfileView
urlpatterns = [
	path("profile/", ReviewerProfileView.as_view(), name="accounts_profile"),

]
