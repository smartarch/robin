from django.contrib import admin
from .models import Review, PublicationList, UserPreferences


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "leader")
    search_fields = ("name", "leader", "description")


@admin.register(PublicationList)
class PublicationListAdmin(admin.ModelAdmin):
    list_display = ("name", "review")
    search_fields = ("name", "review")


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ("user", "default_review", "default_list", "default_page_size")
    search_fields = ("name",)