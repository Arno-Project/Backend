from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.http import JsonResponse

from chat.models import MessageCatalogue, Message
from chat.serializers import MessageSerializer
from accounts.models import User, NormalUser
from notification.notifications import BaseNotification, NewMessageNotification


class ChatsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    notification_builder: BaseNotification = NewMessageNotification

    def get(self, request, peer_id=None):
        user = request.user

        if not peer_id:
            messages = MessageCatalogue().search(user)
        else:
            messages = MessageCatalogue().search(user, peer_id)

        serialized = MessageSerializer(messages, many=True)

        if peer_id:  # if user get messages from one person mark all of them as read
            messages.filter(receiver__user__pk=user.pk).update(is_read=True)

        return JsonResponse(serialized.data, safe=False)

    def post(self, request, peer_id=None):
        if not peer_id:
            return JsonResponse()

        text = request.data.get('text', None)
        if not text:
            return JsonResponse()

        try:
            peer = NormalUser.objects.get(user__pk=peer_id)
            user_n = NormalUser.objects.get(user__pk=request.user.id)
        except NormalUser.DoesNotExist:
            return JsonResponse()

        message = Message(receiver=peer, sender=user_n, text=text,
                          type=Message.MessageType.User)
        message.save()

        self.notification_builder(message).build()

        serialized = MessageSerializer(message)
        return JsonResponse(serialized.data, safe=False)
