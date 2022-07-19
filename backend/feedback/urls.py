from django.urls import path

from feedback.views import SubmitSystemFeedbackView, SearchSystemFeedbackView, SubmitSystemFeedbackReplyView

urlpatterns = [
    path('system/submit/', SubmitSystemFeedbackView.as_view(), name='system-submit'),
    path('system/search/', SearchSystemFeedbackView.as_view(), name='system-search'),
    path('system/reply/submit/', SubmitSystemFeedbackReplyView.as_view(), name='system-reply-submit'),

]
