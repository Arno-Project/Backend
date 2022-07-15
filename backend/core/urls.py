from django.urls import path

from .views import RequestSearchView

urlpatterns = [
    path('request/search/', RequestSearchView.as_view(), name='request_search'),
]
