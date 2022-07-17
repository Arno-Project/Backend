from django.urls import path

from .views import RequestSearchView, LocationView

urlpatterns = [
    path('request/search/', RequestSearchView.as_view(), name='request_search'),
    path('location/', LocationView.as_view(), name='location-create'),
]
