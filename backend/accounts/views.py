import json

from django.contrib.auth import login
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView, LogoutView as KnoxLogoutView
from rest_framework import generics, permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import ModelSerializer

from .models import User, UserCatalogue
from .serializers import CompanyManagerRegisterSerializer, SpecialistRegisterSerializer, CustomerRegisterSerializer, SpecialistFullSerializer, \
    CustomerFullSerializer, TechnicalManagerRegisterSerializer, UserFullSerializer, CompanyManagerFullSerializer, \
    TechnicalManagerFullSerializer


# Create your views here.


class RegisterView(generics.GenericAPIView):

    def get_serializer_class(self):
        role = self.kwargs.get('role')
        if role == User.UserRole.Specialist:
            return SpecialistRegisterSerializer
        elif role == User.UserRole.Customer:
            return CustomerRegisterSerializer
        else:
            raise APIException("Invalid Role", status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        role = self.kwargs.get('role')
        self.serializer_class = self.get_serializer_class()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            **(SpecialistFullSerializer if role == User.UserRole.Specialist else CustomerFullSerializer)(user).data[
                'normal_user'],
            'role': role,
            'token': AuthToken.objects.create(user.normal_user.user)[1]
        })

class ManagerRegisterView(generics.GenericAPIView):

    def get_serializer_class(self):
        role = self.kwargs.get('role')
        if role == User.UserRole.CompanyManager:
            return CompanyManagerRegisterSerializer
        elif role == User.UserRole.TechnicalManager:
            return TechnicalManagerRegisterSerializer
        else:
            raise APIException("Invalid Role", status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        role = self.kwargs.get('role')
        self.serializer_class = self.get_serializer_class()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            # TODO
            **(SpecialistFullSerializer if role == 'specialist' else CustomerFullSerializer)(user).data[
                'normal_user'],
            'role': role,
            'token': AuthToken.objects.create(user.normal_user.user)[1]
        })

class LoginView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        
        res = super(LoginView, self).post(request, format=None)
        if res.status_code == 200:
            return Response({
                **res.data,
                'user': UserFullSerializer(user).data,
                'role': user.get_role()
            })
        return res

class LogoutView(KnoxLogoutView):
    permission_classes = (permissions.IsAuthenticated,)


class MyAccountView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        print(request.user)
        print(format)

        return Response({
            'user': UserFullSerializer(request.user).data,
            'role': request.user.get_role()
        })


class AccountsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self, user) -> ModelSerializer:
        if user.role == User.UserRole.Customer:
            return CustomerFullSerializer
        elif user.role == User.UserRole.Specialist:
            return SpecialistFullSerializer
        elif user.role == User.UserRole.CompanyManager:
            return CompanyManagerFullSerializer
        elif user.role == User.UserRole.TechnicalManager:
            return TechnicalManagerFullSerializer

    def get_complete_user(self, user) -> User:
        print(user.role)
        if user.role == User.UserRole.Customer:
            return user.normal_user_user.customer_normal_user
        elif user.role == User.UserRole.Specialist:
            return user.normal_user_user.specialist_normal_user
        elif user.role == User.UserRole.CompanyManager:
            return user.manager_user_user.company_manager_manager_user
        elif user.role == User.UserRole.TechnicalManager:
            return user.manager_user_user.technical_manager_manger_user

    def get(self, request):
        query_dict = request.GET
        users = UserCatalogue().search(query_dict)
        serialized = [self.get_serializer_class(user)(self.get_complete_user(user)).data for user in users 
            if self.get_serializer_class(user)]
        return JsonResponse({'users': serialized}, safe=False)
