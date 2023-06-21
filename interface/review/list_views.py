# typing packages
from typing import Any

from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.core.paginator import Paginator

# local packages
from .models import Review, PublicationList, UserPreferences


def copy_publication_lists(request: Any, authorized_reviews: Any, publication_list: Any) -> None:
	if request.POST.__contains__("copy_from"):
		copy_from = [int(x) for x in request.POST.get_list("copy_from")]
		authorized_publication_lists = PublicationList.objects.filter(review__in=authorized_reviews)
		clones = authorized_publication_lists.filter(id__in=copy_from)
		for clone in clones:
			for publication in clone.publications:
				if publication not in publication_list.publications.all():
					publication_list.publications.add(publication)

		publication_list.save()


class NewListView(LoginRequiredMixin, CreateView):

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Creates a new publication list
		:param request:
		:param args:
		:param kwargs:
		:return:
		"""
		if not request.POST.__contains__("list_created"):
			return redirect("dashboard_review_all_lists", permanent=True)

		if "review_id" not in kwargs:
			return redirect("dashboard_review_all_lists", permanent=True)

		authorized_reviews = Review.objects.filter(reviewers__in=[request.user])
		review = get_object_or_404(authorized_reviews, id=kwargs["review_id"])

		new_publication_list = PublicationList(name=request.POST.get("list_name"), review=review)
		new_publication_list.save()

		copy_publication_lists(request, authorized_reviews, new_publication_list)

		return redirect("dashboard_review_list", review_id=review.id, list_id=new_publication_list.id, permanent=True)


class CopyListView(LoginRequiredMixin, UpdateView):

	def post(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Creates a new publication list
		:param request:
		:param args:
		:param kwargs:
		:return:
		"""
		if not request.POST.__contains__("list_copied"):
			return redirect("dashboard_review_all_lists", permanent=True)

		if "review_id" not in kwargs:
			return redirect("dashboard_review_all_lists", permanent=True)

		authorized_reviews = Review.objects.filter(reviewers__in=[request.user])
		review = get_object_or_404(authorized_reviews, id=kwargs["review_id"])

		available_publication_lists = PublicationList.objects.filter(review=review)
		publication_list = get_object_or_404(available_publication_lists, id=kwargs['list_id'])

		copy_publication_lists(request, authorized_reviews, publication_list)

		return redirect("dashboard_review_list", review_id=review.id, list_id=publication_list.id, permanent=True)



class ReviewListView(LoginRequiredMixin, TemplateView):
	template_name = "review/review_list.html"

	def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Shows the  [current review] -> [current -> list] -> Publications
		:param request:
		:param args:
		:param kwargs:
		:return:
		"""
		if "review_id" not in kwargs or "list_id" not in kwargs:
			return redirect("dashboard_review_all_lists", permanent=True)

		authorized_reviews = Review.objects.filter(reviewers__in=[request.user])
		review = get_object_or_404(authorized_reviews, id=kwargs["review_id"])
		available_publication_lists = PublicationList.objects.filter(review=review)
		publication_list = get_object_or_404(available_publication_lists, id=kwargs['list_id'])
		user_preference = get_object_or_404(UserPreferences, user=request.user)

		# for paging (for example 25 publications per page)
		paginator = Paginator(publication_list.publications.all().order_by('-id'), user_preference.default_page_size)
		page_number = request.GET.get("page")
		page_obj = paginator.get_page(page_number)

		context = {
			**super().get_context_data(**kwargs),
			"user": request.user,
			"authorized_reviews": authorized_reviews,
			"review": review,
			"available_publication_lists": available_publication_lists,
			"publication_list": publication_list,
			"user_preference": user_preference,
			"page_obj": page_obj,
		}

		return self.render_to_response(context)


class ReviewAllListView(LoginRequiredMixin, View):

	def get(self, request: Any, *args: Any, **kwargs: Any) -> Any:
		"""
		Shows the  [current review] -> [first -> list] -> Publications
		:param request:
		:param args:
		:param kwargs:
		:return:
		"""
		if "review_id" not in kwargs:
			return redirect("dashboard", permanent=True)

		authorized_reviews = Review.objects.filter(reviewers__in=[request.user])
		print (authorized_reviews)
		review = get_object_or_404(authorized_reviews, id=kwargs["review_id"])
		available_publication_lists = PublicationList.objects.filter(review=review)
		if available_publication_lists:
			current_list_id = available_publication_lists[0].id
			return redirect("dashboard_review_list", review_id=review.id, list_id=current_list_id, permanent=True)

		# TODO here we need to deal with reviews with no list
		return redirect("dashboard", permanent=True)


class ListDeleteView(LoginRequiredMixin, DeleteView):
	model = PublicationList

	def post(self, request, *args, **kwargs) -> {}:
		if 'review_id' not in kwargs or 'list_id' not in kwargs:
			return redirect("dashboard_review_all_lists", review_id=kwargs["review_id"], permanent=True)

		fully_authorized_reviews = Review.objects.filter(leader=request.user)
		review = get_object_or_404(fully_authorized_reviews, id=kwargs["review_id"])
		fully_authorized_lists = PublicationList.objects.filter(review=review)
		publication_list = get_object_or_404(fully_authorized_lists, id=kwargs["list_id"])

		if request.POST.__contains__("list_deleted"):
			publication_list.delete()

		return redirect("dashboard_review_all_lists", review_id=kwargs["review_id"], permanent=True)