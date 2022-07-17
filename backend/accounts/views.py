import json
from typing import Type

from django.contrib.auth import login
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView, LogoutView as KnoxLogoutView
from rest_framework import generics, permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import ModelSerializer

from utils.permissions import PermissionFactory
from .models import User, UserCatalogue, Speciality
from .serializers import CompanyManagerRegisterSerializer, CompanyManagerSerializer, CustomerSerializer, \
    SpecialistRegisterSerializer, CustomerRegisterSerializer, SpecialistFullSerializer, \
    CustomerFullSerializer, SpecialistSerializer, TechnicalManagerRegisterSerializer, TechnicalManagerSerializer, \
    UserFullSerializer, CompanyManagerFullSerializer, \
    TechnicalManagerFullSerializer, SpecialitySerializer


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

    def get_serializer_class(self, user, manager) -> Type[
        CustomerFullSerializer | CustomerSerializer |
        SpecialistFullSerializer | SpecialistSerializer |
        CompanyManagerFullSerializer | CompanyManagerSerializer |
        TechnicalManagerFullSerializer | TechnicalManagerSerializer
        ]:
        if user.role == User.UserRole.Customer:
            return CustomerFullSerializer if manager else CustomerSerializer
        elif user.role == User.UserRole.Specialist:
            return SpecialistFullSerializer if manager else SpecialistSerializer
        elif user.role == User.UserRole.CompanyManager:
            return CompanyManagerFullSerializer if manager else CompanyManagerSerializer
        elif user.role == User.UserRole.TechnicalManager:
            return TechnicalManagerFullSerializer if manager else TechnicalManagerSerializer

    def get(self, request):
        manager = request.user.is_manager
        query_dict = request.GET
        users = UserCatalogue().search(query_dict)
        serialized = [self.get_serializer_class(user, manager)(user.full_user).data for user in users]
        return JsonResponse({'users': serialized}, safe=False)


class SpecialityView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        else:
            permission_classes = [PermissionFactory(User.UserRole.CompanyManager).get_permission_class()]
        return [permission() for permission in permission_classes]

    authentication_classes = [TokenAuthentication]

    def get(self, request):
        id_set = set(request.GET.getlist('id'))
        if id_set:
            specialities = Speciality.objects.filter(id__in=id_set)
        else:
            specialities = Speciality.objects.all()
        serialized = SpecialitySerializer(specialities, many=True).data
        return JsonResponse({'specialities': serialized}, safe=False)

    def post(self, request, *args, **kwargs):
        serializer = SpecialitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        speciality = serializer.save()
        return Response({
            'speciality': SpecialitySerializer(speciality).data
        })
