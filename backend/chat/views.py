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
        peer = peer_id
        print("USER1 USER2 ", user, peer, type(user), type(peer))

        if not peer:
            messages = MessageCatalogue().search(user)
        else:
            messages = MessageCatalogue().search(user, peer)
        print("MSG", messages)
        
        serialized = MessageSerializer(messages, many=True)
        return JsonResponse(serialized.data, safe=False)

    def post(self, request):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        msg = serializer.save()
        return JsonResponse({
            'message': MessageSerializer(msg).data
        })
