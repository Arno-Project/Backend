from accounts import serializers
from core.serializers import RequestSerializer
from feedback.models import SystemFeedback, SystemFeedbackReply, EvaluationMetric, Feedback


class EvaluationMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationMetric
        fields = ('id', 'title', 'description', 'user_type')


class SystemFeedbackReplySerializer(serializers.ModelSerializer):
    user = serializers.TechnicalManagerSerializer()

    class Meta:
        model = SystemFeedbackReply
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class SystemFeedbackSerializer(serializers.ModelSerializer):
    reply = SystemFeedbackReplySerializer()
    user = serializers.NormalUserSerializer()

    class Meta:
        model = SystemFeedback
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class FeedbackSerializer(serializers.ModelSerializer):
    metric_scores = EvaluationMetricSerializer(many=True)
    request = RequestSerializer()

    class Meta:
        model = Feedback
        fields = ('id', 'created_at', 'description',
                  'metric_scores', 'request')
