from typing import Type

from django.contrib.auth import login
from django.http import JsonResponse, HttpResponse
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView, LogoutView as KnoxLogoutView
from rest_framework import generics, permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.permissions import PermissionFactory
from .models import User, UserCatalogue, Speciality, Specialist, NormalUser, CompanyManager, ManagerUser, \
    TechnicalManager, Customer
from .serializers import CompanyManagerSerializer, CustomerSerializer, \
    SpecialistFullSerializer, \
    CustomerFullSerializer, SpecialistSerializer, TechnicalManagerSerializer, \
    UserFullSerializer, CompanyManagerFullSerializer, \
    TechnicalManagerFullSerializer, SpecialitySerializer, RegisterSerializerFactory


# Create your views here.


class RegisterView(generics.GenericAPIView):

    def get_serializer_class(self):
        role = self.kwargs.get('role')
        if role == User.UserRole.Specialist:
            return RegisterSerializerFactory(Specialist, NormalUser).get_serializer()
        elif role == User.UserRole.Customer:
            return RegisterSerializerFactory(Customer, NormalUser).get_serializer()
        else:
            raise APIException("Invalid Role", status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        role = self.kwargs.get('role')
        try:
            self.serializer_class = self.get_serializer_class()
        except APIException as e:
            return Response({'error': "Invalid Role"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            **(SpecialistFullSerializer if role == User.UserRole.Specialist else CustomerFullSerializer)(user).data[
                'user'],
            'role': role,
            'token': AuthToken.objects.create(user.normal_user.user)[1]
        })


class ManagerRegisterView(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.CompanyManager).get_permission_class()]

    def get_serializer_class(self):
        role = self.kwargs.get('role')
        if role == User.UserRole.CompanyManager:
            return RegisterSerializerFactory(CompanyManager, ManagerUser).get_serializer()
        elif role == User.UserRole.TechnicalManager:
            return RegisterSerializerFactory(TechnicalManager, ManagerUser).get_serializer()
        else:
            raise APIException("Invalid Role", status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        role = self.kwargs.get('role')
        try:
            self.serializer_class = self.get_serializer_class()
        except APIException as e:
            return Response({'error': "Invalid Role"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            **(CompanyManagerFullSerializer if role == User.UserRole.CompanyManager else CustomerFullSerializer)(
                user).data[
                'user'],
            'role': role,
            'token': AuthToken.objects.create(user.manager_user.user)[1]
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
        return Response({
            'user': UserFullSerializer(request.user).data,
            'role': request.user.get_role()
        })


class EditProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, user_id=''):
        if user_id == '':
            user_id = request.user.id
        if not (
                request.user.role == User.UserRole.CompanyManager or request.user.role == User.UserRole.TechnicalManager):
            if request.user.id != user_id:
                return Response({'error': "You can't edit other users accounts"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(id=user_id)
        for field in ['first_name', 'last_name', 'email', 'phone_number']:
            if field in request.data:
                setattr(user, field, request.data[field])

        if 'password' in request.data:
            user.set_password(request.data['password'])

        user.save()
        serializer = UserFullSerializer(user)

        return Response({
            'user': UserFullSerializer(user).data,
            'role': user.get_role()
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


class SpecialityAddRemoveView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.CompanyManager).get_permission_class() | PermissionFactory(
        User.UserRole.TechnicalManager).get_permission_class() | PermissionFactory(
        User.UserRole.Specialist).get_permission_class()]

    def add_remove_speciality(self, request, is_add, *args, **kwargs):
        print(request.data)
        speciality_id = request.data.get('speciality_id')
        if 'specialist_id' not in request.POST:
            if request.user.role == User.UserRole.Specialist:
                specialist_id = request.user.id
            else:
                raise APIException("Invalid Request", status.HTTP_400_BAD_REQUEST)
        else:
            specialist_id = request.data.get('specialist_id')
        speciality = Speciality.objects.get(pk=speciality_id)
        specialist = UserCatalogue().search(query={'id': specialist_id, 'role': "S"})[
            0].full_user
        # specialist=Specialist.objects.filter(normal_user__user_id=specialist_id).first()
        if is_add:
            specialist.add_speciality(speciality)
        else:
            specialist.remove_speciality(speciality)
        return HttpResponse('OK', status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.add_remove_speciality(request, True, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.add_remove_speciality(request, False, *args, **kwargs)


class ConfirmSpecialistView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.CompanyManager).get_permission_class() | PermissionFactory(
        User.UserRole.TechnicalManager).get_permission_class()]

    def post(self, request, *args, **kwargs):
        specialist_id = request.data.get('specialist_id')
        try:
            specialist = UserCatalogue().search(query={'specialist_id': specialist_id, 'role': "S"})[
                0].full_user
        except IndexError:
            raise APIException("Not Found", status.HTTP_404_NOT_FOUND)
        if specialist.is_validated:
            raise APIException("Specialist already confirmed", status.HTTP_400_BAD_REQUEST)

        request.user.general_user.confirm_specialist(specialist)
        return HttpResponse('OK', status=status.HTTP_200_OK)
