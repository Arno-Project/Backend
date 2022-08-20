from django.urls import path

from accounts.views import NormalRegisterView, ManagerRegisterView, LoginView, LogoutView, MyAccountView, \
    EditProfileView, AccountsView, SpecialityView, SpecialtyCategorizeView, SpecialityAddRemoveView, \
    ConfirmSpecialistView, SpecialitySearchView, DocumentUploadView

urlpatterns = [
    path('register/<slug:role>/', NormalRegisterView.as_view(), name='register'),
    path('manager/register/<slug:role>/', ManagerRegisterView.as_view(), name='manager-register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('my-account/', MyAccountView.as_view(), name='my-account'),
    path('edit/<user_id>/', EditProfileView.as_view(), name='edit-profile'),
    path('edit/', EditProfileView.as_view(), name='edit-profile'),
    path('all/', AccountsView.as_view(), name='all-accounts'),
    path('speciality/', SpecialityView.as_view(), name='speciality'),
    path('speciality/search/', SpecialitySearchView.as_view(), name='speciality-search'),
    path('speciality/categorize/', SpecialtyCategorizeView.as_view(), name='speciality-categorize'),
    path('speciality/<slug:operation>/', SpecialityAddRemoveView.as_view(), name='add-remove-speciality'),
    path('specialist/confirm/', ConfirmSpecialistView.as_view(), name='confirm-specialist'),
    path('specialist/document/',DocumentUploadView.as_view(),name="specialist-document"),

]
