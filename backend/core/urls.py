from django.urls import path

from .views import RequestSearchView, LocationView, RequestSubmitView, RequestCancelByManagerView, RequestStatusView

urlpatterns = [
    path('request/search/', RequestSearchView.as_view(), name='request-search'),
    path('location/', LocationView.as_view(), name='location-create'),
    path('request/submit/', RequestSubmitView.as_view(), name='request-submit'),
    path('request/cancel/force/', RequestCancelByManagerView.as_view(), name='request-cancel'),
    path('request/status/', RequestStatusView.as_view(), name='request-status'),
]
