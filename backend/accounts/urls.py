from django.urls import path

from accounts.views import RegisterView, LoginView, MyAccountView, AccountsView, ManagerRegisterView, LogoutView, \
    SpecialityView

urlpatterns = [
    path('register/<slug:role>/', RegisterView.as_view(), name='register'),
    path('manager/register/<slug:role>/', ManagerRegisterView.as_view(), name='manager-register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('my-account/', MyAccountView.as_view(), name='my-account'),
    path('all/', AccountsView.as_view(), name='all-accounts'),
    path('speciality/', SpecialityView.as_view(), name='create-speciality'),

]
