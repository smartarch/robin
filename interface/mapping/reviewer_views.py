from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View

# from current app
from .models import Review, Comment, UserFieldReview, Mapping, PublicationList


class NewReviewView(LoginRequiredMixin, View):

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:

		if "mapping_id" not in kwargs or "list_id" not in kwargs:
			return redirect("dashboard")

		authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
		current_mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
		authorized_lists = PublicationList.objects.filter(mapping=current_mapping)
		current_list = get_object_or_404(authorized_lists, id=kwargs["list_id"])

		current_review = Review.objects.filter(publication_list=current_list).filter(reviewer=request.user)

		if not current_review and request.POST.__contains__("add_review"):
			review_name = request.POST.get("review_name")
			review = Review(name=review_name)
			review.reviewer = request.user
			review.publication_list = current_list
			review.save()

		return redirect(reverse("publication_list", kwargs={
				"mapping_id": current_mapping.id,
				"list_id": current_list.id}) + "#review")


class EditReviewView(LoginRequiredMixin, View):

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:

		if "mapping_id" not in kwargs or "list_id" not in kwargs:
			return redirect("dashboard")

		authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
		current_mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
		authorized_lists = PublicationList.objects.filter(mapping=current_mapping)
		current_list = get_object_or_404(authorized_lists, id=kwargs["list_id"])

		current_review = Review.objects.filter(publication_list=current_list).filter(reviewer=request.user)

		if request.POST.__contains__("edit_review"):
			review_id = request.POST.getlist("review_id")
			review_name = request.POST.get("review_name")

			if current_review.id == int(review_id):
				current_review.name = review_name
				current_review.save()


		return redirect(reverse("publication_list", kwargs={
				"mapping_id": current_mapping.id,
				"list_id": current_list.id}) + "#review")


