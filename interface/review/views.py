# typing packages
from typing import Any

# django packages
from django.views.generic import TemplateView, CreateView, View, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
# local packages
from .models import Review, PublicationList, UserPreferences
# external packages
import cryptocode
from django.db.models import Q

class CreateUserPreference:

	def find_user_preference (self, user: User, review: Review, publication_list: PublicationList) -> UserPreferences:
		"""
		Finds the selected user default review and default publication list. If it deos not exit, it creates them.
		:param user: Django default user instance which is current request.user (user which is logged in)
		:param review:  An instance of review model; will be the default the review of the user.
		:param publication_list: An instance of current (default) publication list.
		:return: an instance of user preferences which has default review and default publication list
		"""
		user_preferences = UserPreferences.objects.filter(user=user)
		if len(user_preferences) == 0:
			user_preference = UserPreferences(user=user)
			user_preference.default_review = review
			user_preference.default_list = publication_list
			user_preference.save()
		else:
			user_preference = user_preferences[0]
			if not user_preference.default_review and review and publication_list:
				user_preference.default_review = review
				user_preference.default_list = publication_list
				user_preference.save()

		return user_preference


class AllReviewsView(LoginRequiredMixin, TemplateView ):
	template_name = "review/all.html"

	def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		context = super().get_context_data(**kwargs)

		reviews = Review.objects.filter(reviewers__in=[request.user])

		if len(reviews) == 0:
			return redirect("dashboard", permanent=True)

		user_preference = UserPreferences.objects.filter(user=request.user)
		if not user_preference:
			user_preference = UserPreferences(user=request.user)
			user_preference.save()
		else:
			user_preference = user_preference[0]

		context = {
			**context,
			"reviews": reviews,
			"publication_lists": {review.id: PublicationList.objects.filter(review=review) for review in reviews},
			"user_preference": user_preference,
		}

		return self.render_to_response(context)

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		if request.POST.__contains__("made_default"):
			user_preference = get_object_or_404(UserPreferences, user=request.user)

			if request.POST.__contains__("review_id"):
				user_preference.default_review = get_object_or_404(Review, id=request.POST.get("review_id"))

			if request.POST.__contains__("list_id"):
				user_preference.default_list = get_object_or_404(PublicationList, id=request.POST.get("list_id"))
			user_preference.save()

		return redirect("dashboard_all_reviews", permanent=True)
class NewReviewView(LoginRequiredMixin, CreateView, CreateUserPreference):
	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Creates a new review using the form that is passed
		:param request: the current active request sent by a method=POST
		:param args:
		:param kwargs:
		:return: redirects to either newly created review or to the dashboard page.
		"""
		if request.POST.__contains__("review_created"):
			new_review = Review(name=request.POST.get("review_name"))

			if request.POST.__contains__("review_description"):
				new_review.description = request.POST.get("review_description")

			new_review.leader = request.user
			new_review.save()

			new_review.reviewers.add(request.user)
			new_review.secret_key = cryptocode.encrypt(str(new_review.id), "review_id_this_is_for_encryption")
			new_review.save()

			new_publication_list = PublicationList(name="default", review=new_review)
			new_publication_list.save()

			_ = self.find_user_preference(request.user, new_review, new_publication_list)
			return redirect("dashboard_review", review_id=new_review.id, permanent=True)

		return redirect("dashboard_all_reviews", permanent=True)


class JoinReviewView(LoginRequiredMixin, View, CreateUserPreference):

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Join an already created review
		:param request: the current active request sent by a method=POST:
		:param args:
		:param kwargs:
		:return: redirects to either newly joined review or to the dashboard page.
		"""
		if request.POST.__contains__("review_joined"):
			secret_key = request.POST.get("review_secret_key")

			review_id = int(cryptocode.decrypt(str(secret_key), "review_id_this_is_for_encryption"))

			review = get_object_or_404(Review, id=review_id)
			if request.user not in review.reviewers.all():
				review.reviewers.add(request.user)
				review.save()

			publication_list = PublicationList.objects.filter(review=review)[0]

			user_preference = self.find_user_preference(request.user, review, publication_list)
			if not user_preference.default_review:
				user_preference.default_review = review
				user_preference.default_list = publication_list
				user_preference.save()

			return redirect("dashboard_review", review_id=review.id, permanent=True)

		return redirect("dashboard", permanent=True)


class ReviewView(LoginRequiredMixin, TemplateView):
	template_name = "review/single.html"

	def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Shows the current review of the user with review_id
		:param request: request: the current active request sent by a GET request
		:param args:
		:param kwargs:
		:return:
		"""
		context = super().get_context_data(**kwargs)
		if 'review_id' not in kwargs:
			return redirect("dashboard_all_reviews", permanent=True)

		authorized_reviews = Review.objects.filter(reviewers__in=[request.user])
		review = get_object_or_404(authorized_reviews, id=kwargs['review_id'])
		current_publication_lists = PublicationList.objects.filter(review=review)

		publication_list = current_publication_lists[0]

		context['publication_list'] = publication_list
		context['review'] = review
		context['user'] = request.user
		context['is_leader'] = review.leader == request.user

		return self.render_to_response(context)

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		# TODO finish this method
		"""

		:param request:
		:param args:
		:param kwargs:
		:return:
		"""
		context = super().get_context_data(**kwargs)
		if 'review_id' not in kwargs:
			return redirect("dashboard_all_reviews", permanent=True)

		review = get_object_or_404(Review, id=kwargs['id'])
		context['review'] = review
		return self.render_to_response(context)


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
	model = Review

	def post(self, request, *args, **kwargs) -> {}:
		if 'review_id' not in kwargs:
			return redirect("dashboard_all_reviews", permanent=True)

		fully_authorized_reviews = Review.objects.filter(leader=request.user)
		review = get_object_or_404(fully_authorized_reviews, id=kwargs["review_id"])

		if request.POST.__contains__("review_deleted"):
			review.delete()

		return redirect("dashboard_all_reviews", permanent=True)