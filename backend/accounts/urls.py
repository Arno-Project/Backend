from django.urls import path

from accounts.views import RegisterView, LoginView, MyAccountView, UserSearchView, ManagerRegisterView

urlpatterns = [
    path('register/<slug:role>/', RegisterView.as_view(), name='register'),
    path('manager/register/<slug:role>/', ManagerRegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('my-account/', MyAccountView.as_view(), name='my-account'),
    path('search/', UserSearchView.as_view(), name='search'),

]
