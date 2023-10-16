from django.contrib import admin
from .models import Mapping, PublicationList, UserPreferences, UserField, Review, UserFieldReview


@admin.register(Mapping)
class MappingAdmin(admin.ModelAdmin):
    list_display = ("name", "leader")
    search_fields = ("name", "leader", "description")


@admin.register(PublicationList)
class PublicationListAdmin(admin.ModelAdmin):
    list_display = ("name", "mapping")
    search_fields = ("name", "mapping")


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ("user", "default_mapping", "default_list", "default_page_size")
    search_fields = ("name",)


@admin.register(UserField)
class UserFieldAdmin(admin.ModelAdmin):
    list_display = ("caption", "type", "data", "reviewer")
    search_fields = ("caption",)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "reviewer")
    search_fields = ("name",)


@admin.register(UserFieldReview)
class UserFieldReviewAdmin(admin.ModelAdmin):
    list_display = ("reviewer_field","publication", "review", "checked")
    search_fields = ("id",)