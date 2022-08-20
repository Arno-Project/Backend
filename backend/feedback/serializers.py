from accounts import serializers
from core.serializers import RequestSerializer
from feedback.models import SystemFeedback, SystemFeedbackReply, EvaluationMetric, Feedback, MetricScore, ScorePolicy


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


class SystemFeedbackCreationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SystemFeedback
        fields = ('text', 'type', 'status', 'user')


class SystemFeedbackSerializer(serializers.ModelSerializer):
    reply = SystemFeedbackReplySerializer()
    user = serializers.NormalUserFullSerializer()

    class Meta:
        model = SystemFeedback
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class MetricScoreSerializer(serializers.ModelSerializer):
    # metric = EvaluationMetricSerializer()

    class Meta:
        model = MetricScore
        fields = ('metric', 'score')


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ('id', 'created_at', 'description',
                  'metric_scores', 'request', 'user')

        read_only_fields = ('id', 'created_at')
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
        }


class FeedbackReadOnlySerializer(FeedbackSerializer):
    metric_scores = MetricScoreSerializer(many=True)
    user = serializers.NormalUserSerializer()

    class Meta(FeedbackSerializer.Meta):
        model = Feedback
        fields = '__all__'


class ScorePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScorePolicy
        fields = '__all__'
