from django.urls import path

from .views import RequestFinishView, RequestSearchView, LocationView, RequestSubmitView, RequestCancelByManagerView, RequestStatusView, \
    RequestInitialAcceptBySpecialistView, RequestAcceptanceFinalizeByCustomerView, SelectSpecialistForRequestView, \
    RequestAcceptanceFinalizeBySpecialistView, RequestCancelByCustomerView, RequestPopularityView, RequestEditView

urlpatterns = [
    path('request/search/', RequestSearchView.as_view(), name='request-search'),
    path('request/popularity/', RequestPopularityView.as_view(), name='request-popularity'),
    path('location/', LocationView.as_view(), name='location-create'),
    path('request/submit/', RequestSubmitView.as_view(), name='request-submit'),
    path('request/cancel/', RequestCancelByCustomerView.as_view(), name='request-cancel-customer'),
    path('request/cancel/force/', RequestCancelByManagerView.as_view(), name='request-cancel'),
    path('request/status/', RequestStatusView.as_view(), name='request-status'),
    path('request/accept/specialist/initial/', RequestInitialAcceptBySpecialistView.as_view(),
         name='request-initial-accept-by-specialist'),
    path('request/accept/customer/final/', RequestAcceptanceFinalizeByCustomerView.as_view(),
         name='request-finalize-by-customer'),
     path('request/finish/', RequestFinishView.as_view(),
         name='request-finished'),
    path('request/select/specialist/', SelectSpecialistForRequestView.as_view(), name='request-select-specialist'),
    path('request/accept/specialist/final/', RequestAcceptanceFinalizeBySpecialistView.as_view(),
         name='request-finalize-by-specialist'),
    path('request/edit/<request_id>/', RequestEditView.as_view(), name='edit-request'),
]
