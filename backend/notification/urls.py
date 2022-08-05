from django.urls import path

from notification.views import NotificationView

urlpatterns = [
    path('', NotificationView.as_view(), name='notification-view-unread'),
    path('<notification_id>/', NotificationView.as_view(), name='notification-view'),
]
