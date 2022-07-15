from accounts import serializers
from feedback.models import SystemFeedback


class SystemFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemFeedback
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }