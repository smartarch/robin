from rest_framework.authentication import BasicAuthentication
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import Reviewer
from .serializers import ReviewerSerializer


class ReviewerProfileView(APIView):
    queryset = Reviewer.objects.all()

    def get(self, request, *args, **kwargs):

        user = get_object_or_404(self.queryset, pk=request.user.pk)

        # Retrieve the user's token
        token, created = Token.objects.get_or_create(user=user)

        # Serialize the token data
        user_data = {
            'user': ReviewerSerializer(user, context={'request': request}).data,
            'token': token.key,
        }

        return Response(user_data)
