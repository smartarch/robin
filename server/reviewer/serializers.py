from rest_framework import serializers
from .models import Reviewer


class ReviewerSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Reviewer
        fields = ['email', 'short_name', 'photo']
