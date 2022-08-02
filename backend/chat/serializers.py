from rest_framework.serializers import ModelSerializer
from backend.accounts.serializers import NormalUserSerializer

from .models import Message


class MessageSerializer(ModelSerializer):
    receiver = NormalUserSerializer()
    sender = NormalUserSerializer()

    class Meta:
        model = Message
        fields = '__all__'
