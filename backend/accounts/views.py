import json

from django.contrib.auth import login
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from rest_framework import generics, permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, UserCatalogue
from .serializers import SpecialistRegisterSerializer, CustomerRegisterSerializer, SpecialistFullSerializer, \
    CustomerFullSerializer, UserFullSerializer, CompanyManagerFullSerializer, \
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

        print(request.data)

        if User.objects.filter(email=request.POST.get('email')).exists():
            return Response({
                'email': [_('User with this email address already exists.')]
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        print((SpecialistFullSerializer if role == 'specialist' else CustomerFullSerializer)(user).data)
        return Response({
            'normal_user': (SpecialistFullSerializer if role == 'specialist' else CustomerFullSerializer)(user).data[
                'normal_user'],
            'role': role,
            'token': AuthToken.objects.create(user.normal_user.user)[1]
        })

class ManagerRegisterView(generics.GenericAPIView):

    def get_serializer_class(self):
        role = self.kwargs.get('role')
        if role == 'specialist':
            return SpecialistRegisterSerializer
        elif role == 'customer':
            return CustomerRegisterSerializer
        else:
            raise APIException("Invalid Role", status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        role = self.kwargs.get('role')
        self.serializer_class = self.get_serializer_class()

        serializer = self.get_serializer(data=request.data)

        if User.objects.filter(email=request.data['email']).exists():
            return Response({
                'email': [_('User with this email address already exists.')]
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'normal_user': (SpecialistFullSerializer if role == 'specialist' else CustomerFullSerializer)(user).data[
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


class UserSearchView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self, user):
        if user.role == User.UserRole.Customer[0]:
            return CustomerFullSerializer
        elif user.role == User.UserRole.Specialist[0]:
            return SpecialistFullSerializer
        elif user.role == User.UserRole.CompanyManager[0]:
            return CompanyManagerFullSerializer
        elif user.role == User.UserRole.TechnicalManager[0]:
            return TechnicalManagerFullSerializer

    def get_complete_user(self, user):
        if user.role == User.UserRole.Customer[0]:
            return user.normal_user_user.customer_normal_user
        elif user.role == User.UserRole.Specialist[0]:
            return user.normal_user_user.specialist_normal_user
        elif user.role == User.UserRole.CompanyManager[0]:
            return user.manager_user_user.company_manager_manager_user
        elif user.role == User.UserRole.TechnicalManager[0]:
            return user.manager_user_user.technical_manager_manger_user

    def get(self, request):
        print(request.GET)
        users = UserCatalogue().search(json.loads(request.GET.get('q')))
        serialized = [self.get_serializer_class(user)(self.get_complete_user(user)).data for user in users]
        return JsonResponse(serialized, safe=False)
