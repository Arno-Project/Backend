from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.http import JsonResponse

from chat.models import MessageCatalogue
from chat.serializers import MessageSerializer


class ChatsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, peer_id=None):
        user = request.user

        if not peer_id:
            messages = MessageCatalogue().search(user)
        else:
            messages = MessageCatalogue().search(user, peer_id)
        
        serialized = MessageSerializer(messages, many=True)

        if peer_id: # if user get messages from one person mark all of them as read
            messages.filter(receiver__user__pk=user.pk).update(is_read=True)

        return JsonResponse(serialized.data, safe=False)

    def post(self, request):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        msg = serializer.save()
        return JsonResponse({
            'message': MessageSerializer(msg).data
        })
