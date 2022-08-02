from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.http import JsonResponse

from backend.chat.models import MessageCatalogue
from backend.chat.serializers import MessageSerializer


class ChatsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user1 = request.GET.get('user1', None)
        user2 = request.GET.get('user2', None)
        if not user1:
            return ""  # TODO

        if not user2:
            messages = MessageCatalogue().search(user1)
        else:
            messages = MessageCatalogue().search(user1, user2)

        serialized = MessageSerializer(messages, many=True)
        return JsonResponse(serialized.data)

    def post(self, request):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        msg = serializer.save()
        return JsonResponse({
            'message': MessageSerializer(msg).data
        })
