from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import ReviewerCreationForm, ReviewerChangeForm
from .models import Reviewer


class ReviewerAdmin(UserAdmin):
    add_form = ReviewerCreationForm
    form = ReviewerChangeForm
    model = Reviewer
    list_display = ("email", "is_staff", "is_active",)
    list_filter = ("email", "is_staff", "is_active",)
    fieldsets = (
        (None, {"fields": ("email", "password", "first_name", "last_name")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "password1", "password2", "is_staff",
                "is_active", "groups", "user_permissions", "first_name", "last_name"
            )}
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)


admin.site.register(Reviewer, ReviewerAdmin)
