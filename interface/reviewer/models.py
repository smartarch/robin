from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import ReviewerManager


class Reviewer(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = ReviewerManager()

    def __str__(self):
        return self.email

    def short_name(self):
        if self.first_name:
            return self.first_name
        if self.last_name:
            return self.last_name
        return self.email.split('@')[0]

