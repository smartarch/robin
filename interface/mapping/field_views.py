from typing import Any, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import DeleteView, UpdateView
from django.http import HttpRequest, HttpResponse

# from current app
from .models import ReviewField, Mapping, PublicationList, ReviewFieldValue, ReviewFieldValueCoding


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
            new_field = ReviewField(name=field_name, type=field_type, mapping=current_mapping)
            new_field.save()

        return redirect(reverse("publication_list", kwargs={
            "mapping_id": current_mapping.id,
            "list_id": current_list.id}) + "#fields")


class EditFieldsView(LoginRequiredMixin, UpdateView, DeleteView):
    model = ReviewField

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:

        if "mapping_id" not in kwargs or "list_id" not in kwargs:
            return redirect("publication_list_all")

        authorized_mappings = Mapping.objects.filter(reviewers__in=[request.user])
        current_mapping = get_object_or_404(authorized_mappings, id=kwargs["mapping_id"])
        authorized_lists = PublicationList.objects.filter(mapping=current_mapping)
        current_list = get_object_or_404(authorized_lists, id=kwargs["list_id"])
        authorized_fields = ReviewField.objects.filter(mapping=current_mapping)

        if "edit_fields" in request.POST:
            field_ids = request.POST.getlist("field_ids")
            field_names = request.POST.getlist("field_names")

            for field_id, field_name in zip(field_ids, field_names):
                field = get_object_or_404(authorized_fields, id=field_id)
                field.name = field_name
                field.save()

        if "delete_field" in request.POST:
            field_id = request.POST.get("delete_field")
            field = get_object_or_404(authorized_fields, id=field_id)
            field.delete()

        if "duplicate_field" in request.POST:
            field_id = request.POST.get("duplicate_field")
            field = get_object_or_404(authorized_fields, id=field_id)
            field.duplicate()

        if "rename_code" in request.POST:
            original_code = request.POST.get("original_code")
            new_code = request.POST.get("code")
            field_id = request.POST.get("field_id")
            field = get_object_or_404(authorized_fields, id=field_id)
            ReviewFieldValueCoding.rename_code(field, original_code, new_code)

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

        review_fields: list[ReviewField] = ReviewField.objects.filter(mapping=current_mapping)

        for field in review_fields:
            new_value = request.POST.get(f"review_field_{field.id}")
            field.get_value_class().save_value(field, publication, new_value)

        return HttpResponse("fields_saved")
