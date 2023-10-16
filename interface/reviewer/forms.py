from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import Reviewer


class ReviewerCreationForm(UserCreationForm):

    class Meta:
        model = Reviewer
        fields = ("email",)


class ReviewerChangeForm(UserChangeForm):

    class Meta:
        model = Reviewer
        fields = ("email",)
