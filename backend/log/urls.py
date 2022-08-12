from django.urls import path

from log.views import LogSearchView

urlpatterns = [
    path('search/', LogSearchView.as_view(), name='log-search'),
]
