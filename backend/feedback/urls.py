from django.urls import path

from feedback.views import SubmitSystemFeeedbackView, SearchSystemFeeedbackView, SubmitSystemFeedbackReplyView

urlpatterns = [
    path('system/submit/', SubmitSystemFeeedbackView.as_view(), name='system-submit'),
    path('system/search/', SearchSystemFeeedbackView.as_view(), name='system-search'),
    path('system/reply/submit/', SubmitSystemFeedbackReplyView.as_view(), name='system-reply-submit'),

]
