from typing import Any, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import DeleteView, UpdateView
from django.http import HttpRequest

# from current app
from .models import ReviewField, Mapping, PublicationList, ReviewFieldValue


class NewReviewFieldView(LoginRequiredMixin, View):

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:

        if "mapping_id" not in kwargs or "list_id" not in kwargs:
            return redirect("publication_list_all")

        authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
        current_mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
        authorized_lists = PublicationList.objects.filter(mapping=current_mapping)
        current_list = get_object_or_404(authorized_lists, id=kwargs["list_id"])

        if request.POST.__contains__("add_field"):
            field_name = request.POST.get("field_name")
            field_type = request.POST.get("field_type")
            new_field = ReviewField(name=field_name, type=field_type, publication_list=current_list)
            new_field.save()

        return redirect(reverse("publication_list", kwargs={
            "mapping_id": current_mapping.id,
            "list_id": current_list.id}) + "#fields")


class EditFieldsView(LoginRequiredMixin, UpdateView, DeleteView):
    model = ReviewField

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:

        if "mapping_id" not in kwargs or "list_id" not in kwargs:
            return redirect("publication_list_all")

        authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
        current_mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
        authorized_lists = PublicationList.objects.filter(mapping=current_mapping)
        current_list = get_object_or_404(authorized_lists, id=kwargs["list_id"])
        authorized_fields = ReviewField.objects.filter(publication_list=current_list)

        if request.POST.__contains__("edit_fields"):
            field_ids = request.POST.getlist("field_ids")
            field_names = request.POST.getlist("field_names")

            for field_id, field_name in zip(field_ids, field_names):
                field = get_object_or_404(authorized_fields, id=field_id)
                field.name = field_name
                field.save()

        if request.POST.__contains__("delete_field"):
            field_id = request.POST.getlist("delete_field")[0]
            field = get_object_or_404(authorized_fields, id=field_id)
            field.delete()

        return redirect(reverse("publication_list", kwargs={
            "mapping_id": current_mapping.id,
            "list_id": current_list.id}) + "#fields")


class FieldReviewView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:

        if "mapping_id" not in kwargs or "list_id" not in kwargs:
            return redirect("dashboard")

        authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
        current_mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
        authorized_lists = PublicationList.objects.filter(mapping=current_mapping)
        current_list = get_object_or_404(authorized_lists, id=kwargs["list_id"])

        publication_id = request.POST.get("publication_id")
        publication = get_object_or_404(current_list.publications, id=publication_id)

        review_fields: list[ReviewField] = ReviewField.objects.filter(publication_list=current_list)

        for field in review_fields:
            value: Optional[ReviewFieldValue] = field.get_value_class().objects.filter(publication=publication).filter(review_field=field).first()
            new_value = request.POST.get(f"review_field_{field.id}")

            if value:
                if new_value == "":  # new value is empty -> remove previous value object
                    value.delete()
                else:  # update previous value object
                    value.set_value(new_value)
                    value.save()
            elif new_value != "":  # create new value object
                value = field.get_value_class()(review_field=field, publication=publication)
                value.set_value(new_value)
                value.save()

        return redirect(reverse("publication_list", kwargs={
            "mapping_id": current_mapping.id,
            "list_id": current_list.id}))