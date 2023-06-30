from django.contrib import admin
from .models import QueryPlatform, Query


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ("query", "platform", "created_at")
    search_fields = ("query", )


@admin.register(QueryPlatform)
class QueryPlatformAdmin(admin.ModelAdmin):
    list_display = ("source", "user")
    search_fields = ("source",)
