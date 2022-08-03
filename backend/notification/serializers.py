from accounts import serializers
from notification.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.UserSerializer()

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id', 'date')
        extra_kwargs = {
            'id': {'read_only': True},
            'date': {'read_only': True},
        }
