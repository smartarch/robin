from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import DeleteView, UpdateView

# from current app
from .models import UserField, Mapping, PublicationList, UserFieldReview, Review


class NewFieldView(LoginRequiredMixin, View):

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:

		if "mapping_id" not in kwargs or "list_id" not in kwargs:
			return redirect("publication_list_all")

		authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
		current_mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
		authorized_lists = PublicationList.objects.filter(mapping=current_mapping)
		current_list = get_object_or_404(authorized_lists, id=kwargs["list_id"])


		if request.POST.__contains__("add_field"):
			field_caption = request.POST.get("field_caption")
			field_value = request.POST.get("field_value")
			field_type = request.POST.get("field_type")
			new_field = UserField(caption=field_caption)
			new_field.type = field_type
			new_field.data = field_value
			try:
				_ = new_field.data
			except ValueError:
				new_field.type = "T"
				new_field.data = field_value

			new_field.reviewer = request.user
			new_field.publication_list = current_list
			new_field.save()

		return redirect(reverse("publication_list", kwargs={
				"mapping_id": current_mapping.id,
				"list_id": current_list.id}) + "#fields")

class EditFieldsView(LoginRequiredMixin,UpdateView, DeleteView):
	model = UserField

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:

		if "mapping_id" not in kwargs or "list_id" not in kwargs:
			return redirect("publication_list_all")

		authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
		current_mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
		authorized_lists = PublicationList.objects.filter(mapping=current_mapping)
		current_list = get_object_or_404(authorized_lists, id=kwargs["list_id"])
		authorized_fields = UserField.objects.filter(publication_list=current_list)

		if request.POST.__contains__("edit_fields"):
			field_ids = request.POST.getlist("field_ids")
			field_captions = request.POST.getlist("field_captions")
			field_values = request.POST.getlist("field_values")

			for field_id, field_caption, field_value in zip(field_ids, field_captions, field_values):
				field = get_object_or_404(authorized_fields, id=field_id)
				field.caption = field_caption
				field.data = field_value
				try:
					_ = field.data
				except ValueError:
					field.type = "Text"
					field.data = field_value
				field.save()

		if request.POST.__contains__("delete_field"):
			field_id = request.POST.getlist("delete_field")[0]
			field = get_object_or_404(authorized_fields, id=field_id)
			field.delete()

		return redirect(reverse("publication_list", kwargs={
				"mapping_id": current_mapping.id,
				"list_id": current_list.id}) + "#fields")


class FieldReviewView(LoginRequiredMixin, View):

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:

		if "mapping_id" not in kwargs or "list_id" not in kwargs:
			return redirect("dashboard")

		authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
		current_mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
		authorized_lists = PublicationList.objects.filter(mapping=current_mapping)
		current_list = get_object_or_404(authorized_lists, id=kwargs["list_id"])

		reviews = Review.objects.filter(publication_list=current_list)
		review = get_object_or_404(reviews, reviewer=request.user)

		publication_id = request.POST.getlist("save_field_reviews")[0]
		publication = get_object_or_404(current_list.publications, id=publication_id)

		all_fields = UserField.objects.filter(publication_list=current_list)
		verified_field = [int(x) for x in request.POST.getlist(f"verify_checkbox_{publication_id}")]

		print (verified_field)
		for field in all_fields:
			user_fields = UserFieldReview.objects.filter(
				publication=publication).filter(review=review).filter(reviewer_field=field)

			if user_fields:
				user_field = user_fields[0]
				if user_field.reviewer_field.id in verified_field:
					user_field.checked = True
				else:
					user_field.checked = False
				user_field.save()
			else:
				user_field = UserFieldReview()
				user_field.reviewer_field = field
				user_field.review = review
				user_field.publication = publication
				user_field.save()

				if user_field.reviewer_field.id in verified_field:
					user_field.checked = True
					user_field.save()

		return redirect(reverse("publication_list", kwargs={
				"mapping_id": current_mapping.id,
				"list_id": current_list.id}))