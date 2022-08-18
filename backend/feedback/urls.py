from django.urls import path

from feedback.views import SubmitSystemFeedbackView, SearchSystemFeedbackView, SubmitSystemFeedbackReplyView, \
    EvaluationMetricView, FeedbackView, ForceUpdateScoresView

urlpatterns = [
    path('system/submit/', SubmitSystemFeedbackView.as_view(), name='system-submit'),
    path('system/search/', SearchSystemFeedbackView.as_view(), name='system-search'),
    path('system/reply/submit/', SubmitSystemFeedbackReplyView.as_view(), name='system-reply-submit'),
    path('metric/', EvaluationMetricView.as_view(), name='evaluation-metric'),
    path('metric/<evaluation_metric_id>/', EvaluationMetricView.as_view(), name='evaluation-metric'),
    path('request/', FeedbackView.as_view(), name='feedback'),
    path('request/<service_request_id>/', FeedbackView.as_view(), name='feedback'),
    path('score/force-update/', ForceUpdateScoresView.as_view(), name='score-update-all'),
    path('score/force-update/<user_id>/', ForceUpdateScoresView.as_view(), name='score-update'),
]
