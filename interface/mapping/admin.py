from django.contrib import admin
from .models import Mapping, PublicationList, UserPreferences, ReviewField, ReviewFieldValueText, ReviewFieldValueNumber


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


@admin.register(ReviewField)
class ReviewFieldAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    search_fields = ("name",)


@admin.register(ReviewFieldValueText)
class ReviewFieldValueTextAdmin(admin.ModelAdmin):
    list_display = ("review_field", "publication", "value")
    search_fields = ("id",)


@admin.register(ReviewFieldValueNumber)
class ReviewFieldValueNumberAdmin(admin.ModelAdmin):
    list_display = ("review_field", "publication", "value")
    search_fields = ("id",)
