import json
import os
import uuid
from abc import ABC
from typing import Type

from django.contrib.auth import login
from django.core.files.base import ContentFile
from django.http import JsonResponse, HttpResponse

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView, LogoutView as KnoxLogoutView
from rest_condition import Or, And
from rest_framework import generics, permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import APIException
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView

from feedback.models import FeedbackCatalogue
from feedback.serializers import EvaluationMetricSerializer, FeedbackReadOnlySerializer
from accounts.constants import *
from arno.settings import MEDIA_ROOT
from log.models import Logger
from utils.permissions import PermissionFactory, IsReadyOnlyRequest, IsPostRequest
from .models import User, UserCatalogue, Speciality, Specialist, NormalUser, CompanyManager, ManagerUser, \
    TechnicalManager, Customer, SpecialityCatalogue
from .serializers import CompanyManagerSerializer, CustomerSerializer, \
    SpecialistFullSerializer, \
    CustomerFullSerializer, SpecialistSerializer, TechnicalManagerSerializer, \
    UserFullSerializer, CompanyManagerFullSerializer, \
    TechnicalManagerFullSerializer, SpecialitySerializer, RegisterSerializerFactory, SpecialityCreationSerializer


class RegisterView(generics.GenericAPIView, ABC):
    first_serializer = None
    second_serializer = None
    first_serializer_role = None
    attribute_name = ''

    def __init__(self, first_serializer, second_serializer, first_serializer_role, attribute_name):
        super().__init__()
        self.first_serializer = first_serializer
        self.second_serializer = second_serializer
        self.first_serializer_role = first_serializer_role
        self.attribute_name = attribute_name

    def get_serializer_class(self):
        pass

    @Logger().log_name()
    def post(self, request, *args, **kwargs):
        role = self.kwargs.get('role')
        try:
            self.serializer_class = self.get_serializer_class()
        except APIException as e:
            return JsonResponse({'error': INVALID_ROLE}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return JsonResponse({
            **(self.first_serializer if role == self.first_serializer_role else self.second_serializer)(user).data[
                'user'],
            'role': role,
            'token': AuthToken.objects.create(getattr(user, self.attribute_name).user)[1]
        })


class NormalRegisterView(RegisterView):

    def __init__(self):
        super(NormalRegisterView, self).__init__(SpecialistFullSerializer, CustomerFullSerializer,
                                                 User.UserRole.Specialist, 'normal_user')

    def get_serializer_class(self):
        role = self.kwargs.get('role')
        if role == User.UserRole.Specialist:
            return RegisterSerializerFactory(Specialist, NormalUser).get_serializer()
        elif role == User.UserRole.Customer:
            return RegisterSerializerFactory(Customer, NormalUser).get_serializer()
        else:
            raise APIException(INVALID_ROLE, status.HTTP_400_BAD_REQUEST)


class ManagerRegisterView(RegisterView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(
        User.UserRole.CompanyManager).get_permission_class()]

    def __init__(self):
        super(ManagerRegisterView, self).__init__(CompanyManagerFullSerializer, TechnicalManagerFullSerializer,
                                                  User.UserRole.CompanyManager, 'manager_user')

    def get_serializer_class(self):
        role = self.kwargs.get('role')
        if role == User.UserRole.CompanyManager:
            return RegisterSerializerFactory(CompanyManager, ManagerUser).get_serializer()
        elif role == User.UserRole.TechnicalManager:
            return RegisterSerializerFactory(TechnicalManager, ManagerUser).get_serializer()
        else:
            raise APIException(INVALID_ROLE, status.HTTP_400_BAD_REQUEST)


class LoginView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    @Logger().log_name()
    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        res = super(LoginView, self).post(request, format=None)
        if res.status_code == 200:
            return JsonResponse({
                **res.data,
                'user': UserFullSerializer(user).data,
                'role': user.get_role()
            })
        return res


class LogoutView(KnoxLogoutView):
    permission_classes = (permissions.IsAuthenticated,)

    @Logger().log_name()
    def post(self, request, format=None):
        return super(LogoutView, self).post(request, format=None)


class MyAccountView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return JsonResponse({
            'user': UserFullSerializer(request.user).data,
            'role': request.user.get_role(),
            'is_validated': request.user.role != User.UserRole.Specialist or request.user.normal_user_user.specialist_normal_user.get_is_validated()
        })


class EditProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @Logger().log_name()
    def put(self, request, user_id=''):
        if user_id == '':
            user_id = request.user.id
        if not (
                request.user.get_role() == User.UserRole.CompanyManager
                or request.user.get_role() == User.UserRole.TechnicalManager
        ):
            if int(request.user.id) != int(user_id):
                return JsonResponse({'error': EDIT_OTHER_USER_ACCOUNT_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(id=user_id)
        for field in ['first_name', 'last_name', 'email', 'phone_number']:
            if field in request.data:
                setattr(user, field, request.data[field])

        if 'password' in request.data:
            if 'old_password' not in request.data:
                return JsonResponse({'error': OLD_PASSWORD_NOT_PROVIDED_ERROR}, status=status.HTTP_400_BAD_REQUEST)
            if not user.check_password(request.data['old_password']):
                return JsonResponse({'error': OLD_PASSWORD_NOT_MATCH_ERROR}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(request.data['password'])

        if user.role == User.UserRole.Specialist:
            if 'is_active' in request.data:
                is_active = request.data.get('is_active', True)
                user.full_user.set_active(is_active)
                user.full_user.save()

        user.save()

        return JsonResponse({
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
        if user.get_role() == User.UserRole.Customer:
            return CustomerFullSerializer if manager else CustomerSerializer
        elif user.get_role() == User.UserRole.Specialist:
            return SpecialistFullSerializer if manager else SpecialistSerializer
        elif user.get_role() == User.UserRole.CompanyManager:
            return CompanyManagerFullSerializer if manager else CompanyManagerSerializer
        elif user.get_role() == User.UserRole.TechnicalManager:
            return TechnicalManagerFullSerializer if manager else TechnicalManagerSerializer

    @Logger().log_name()
    def get(self, request):
        manager = request.user.is_manager
        query_dict = request.query_params.dict()
        query_dict_ = {**query_dict, 'requester_type': request.user.get_role()}
        users = UserCatalogue().search(query_dict_)

        serialized = [self.get_serializer_class(user, manager)(
            user.full_user).data for user in users]
        return JsonResponse({'users': serialized}, safe=False)


class SpecialityView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        else:
            permission_classes = [
                PermissionFactory(User.UserRole.CompanyManager).get_permission_class() |
                PermissionFactory(User.UserRole.TechnicalManager).get_permission_class() |
                PermissionFactory(
                    User.UserRole.Specialist).get_permission_class()
            ]
        return [permission() for permission in permission_classes]

    authentication_classes = [TokenAuthentication]

    @Logger().log_name()
    def get(self, request):
        id_set = set(request.GET.getlist('id'))
        if id_set:
            specialities = Speciality.objects.filter(id__in=id_set)
        else:
            specialities = Speciality.objects.all()
        serialized = SpecialitySerializer(specialities, many=True).data
        return JsonResponse({'specialities': serialized}, safe=False)

    @Logger().log_name()
    def post(self, request, *args, **kwargs):
        speciality = SpecialityCatalogue().search(
            query={'title': request.data.get('title')})
        if speciality.exists() and speciality.first().get_title() == request.data.get('title'):
            return JsonResponse({'error': SPECIALITY_EXISTS_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        if request.data.get('parent', None):
            speciality = SpecialityCatalogue().search(
                query={'id': request.data.get('parent')})
            if speciality.exists():
                request.data['parent'] = speciality.first().id
                if speciality.first().parent is not None:
                    return JsonResponse({'error': SPECIALITY_PARENT_ERROR}, status=status.HTTP_400_BAD_REQUEST)
            else:
                request.data['parent'] = None
        else:
            request.data['parent'] = None
        if (request.user.get_role() == User.UserRole.Specialist) and request.data.get('parent', None) is None:
            return JsonResponse({'error': SPECIALITY_SPECIALIST_PARENT_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        print(request.data)
        serializer = SpecialityCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        speciality = serializer.save()
        return Response({
            'speciality': SpecialitySerializer(speciality).data
        })


class SpecialitySearchView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @Logger().log_name()
    def get(self, request):
        query = json.loads(request.GET.get('q'))
        print(query)
        specialities = SpecialityCatalogue().search(query)
        serialized = SpecialitySerializer(specialities, many=True).data
        return JsonResponse({'specialities': serialized}, safe=False)


class SpecialtyCategorizeView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [
        PermissionFactory(User.UserRole.CompanyManager).get_permission_class() |
        PermissionFactory(
            User.UserRole.TechnicalManager).get_permission_class()
    ]

    def post(self, request, *args, **kwargs):
        parent_id = request.data.get('parent', None)
        child_id = request.data.get('child', None)
        if parent_id is None or child_id is None:
            return JsonResponse({'error': INVALID_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        if parent_id == child_id:
            return JsonResponse({'error': SPECIALITY_CHILD_EQUAL_PARENT_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        parent = SpecialityCatalogue().search(query={'id': parent_id})
        child = SpecialityCatalogue().search(query={'id': child_id})
        if not parent.exists() or not child.exists():
            return JsonResponse({'error': SPECIALITY_NOT_EXISTS_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        child = child.first()
        parent = parent.first()
        if parent.parent is not None:
            return JsonResponse({'error': SPECIALITY_PARENT_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        child.parent = parent
        child.save()
        return JsonResponse({'speciality': SpecialitySerializer(child).data})


class SpecialityAddRemoveView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.CompanyManager).get_permission_class() | PermissionFactory(
        User.UserRole.TechnicalManager).get_permission_class() | PermissionFactory(
        User.UserRole.Specialist).get_permission_class()]

    def add_remove_speciality(self, request, is_add, *args, **kwargs):
        print(request.data)
        speciality_id = request.data.get('speciality_id')
        if 'specialist_id' not in request.data:
            if request.user.get_role() == User.UserRole.Specialist:
                specialist_id = request.user.id
            else:
                return JsonResponse({'error': INVALID_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        else:
            specialist_id = request.data.get('specialist_id')
        speciality = Speciality.objects.get(pk=speciality_id)
        specialist = UserCatalogue().search(query={'id': specialist_id, 'role': "S"})[
            0].full_user
        if is_add:
            specialist.add_speciality(speciality)
        else:
            specialist.remove_speciality(speciality)
        return HttpResponse('OK', status=status.HTTP_200_OK)

    @Logger().log_name()
    def post(self, request, operation="", *args, **kwargs):
        if operation == "add":
            return self.add_remove_speciality(request, True, *args, **kwargs)
        elif operation == "delete":
            return self.add_remove_speciality(request, False, *args, **kwargs)
        else:
            return JsonResponse({'error': INVALID_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

    @Logger().log_name()
    def delete(self, request, *args, **kwargs):
        return self.add_remove_speciality(request, False, *args, **kwargs)


class ConfirmSpecialistView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.CompanyManager).get_permission_class() | PermissionFactory(
        User.UserRole.TechnicalManager).get_permission_class()]

    @Logger().log_name()
    def post(self, request, *args, **kwargs):
        specialist_id = request.data.get('specialist_id')
        try:
            specialist = UserCatalogue().search(
                query={'id': specialist_id, 'role': "S"})[0].full_user
        except IndexError:
            return JsonResponse({'error': SPECIALIST_NOT_FOUND_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        if specialist.get_is_validated():
            return JsonResponse({'error': SPECIALIST_ALREADY_CONFIRMED_ERROR}, status=status.HTTP_400_BAD_REQUEST)

        request.user.general_user.confirm_specialist(specialist)
        return HttpResponse('OK', status=status.HTTP_200_OK)


class DocumentUploadView(APIView):
    parser_classes = (MultiPartParser,)
    authentication_classes = [TokenAuthentication]
    permission_classes = [
        Or(
            And(IsReadyOnlyRequest, PermissionFactory(
                User.UserRole.TechnicalManager).get_permission_class()),
            And(IsReadyOnlyRequest, PermissionFactory(
                User.UserRole.CompanyManager).get_permission_class()),
            PermissionFactory(User.UserRole.Specialist).get_permission_class())
    ]

    def check_for_media_dir(self):
        if not os.path.isdir(MEDIA_ROOT):
            os.makedirs(MEDIA_ROOT)

    @Logger().log_name()
    def post(self, request, format=''):
        up_file = request.FILES['file']

        # up file name without extension
        file_name = up_file.name[:up_file.name.rfind('.')]
        extension = up_file.name[up_file.name.rfind('.') + 1:]
        full_name = file_name + '-' + str(uuid.uuid4()) + '.' + extension

        self.check_for_media_dir()
        with open(MEDIA_ROOT + "/" + full_name, 'wb+') as destination:
            for chunk in up_file.chunks():
                destination.write(chunk)
        spec = request.user.full_user
        with open(MEDIA_ROOT + "/" + full_name, 'rb') as fh:
            with ContentFile(fh.read()) as file_content:
                spec.documents.save(full_name, file_content)
                spec.save()

        return Response(up_file.name, HTTP_201_CREATED)

    @Logger().log_name()
    def get(self, request):
        specialist_id = request.query_params.get('id') if request.user.get_role() != User.UserRole.Specialist \
            else request.user.id
        try:
            specialist = User.objects.get(pk=specialist_id).full_user
        except User.DoesNotExist:
            return JsonResponse({'error': SPECIALIST_NOT_FOUND_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        doc: str = specialist.documents.path
        index = doc.find('/media')
        return JsonResponse({'document': doc[index:]}, status=status.HTTP_200_OK)


class UserSatisfactionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(
        User.UserRole.CompanyManager).get_permission_class()]

    @Logger().log_name()
    def get(self, request):
        query = json.loads(request.GET.get('q'))
        role = query.get('role', User.UserRole.Customer)
        threshold = query.get('threshold', 50)
        after = query.get('after', None)
        ordering = query.get('ordering', 'avg')

        if role not in [User.UserRole.Customer, User.UserRole.Specialist]:
            return JsonResponse({'error': INVALID_ROLE}, status=status.HTTP_400_BAD_REQUEST)

        users = UserCatalogue().search({'role': role})
        print(users)

        user_serialized_data = []
        if role == User.UserRole.Customer:
            user_serialized_data = [CustomerFullSerializer(
                u.full_user).data for u in users]
        else:
            user_serialized_data = [SpecialistFullSerializer(
                u.full_user).data for u in users]

        result = []
        for i, user in enumerate(users):
            feedback_query = {'user': user.id}
            if after:
                feedback_query['after'] = after
            user_feedbacks = FeedbackCatalogue().search(feedback_query)

            bad_feedbacks = []
            bad_metrics = set()
            average_sum = 0
            for feedback in user_feedbacks:
                average_sum += feedback.get_average_score()
                if feedback.get_average_score() < threshold:
                    bad_feedbacks.append(feedback)
                for metric_score in feedback.metric_scores.all():
                    if metric_score.score < threshold:
                        bad_metrics.add(metric_score.metric)

            if len(bad_feedbacks) > 0 or len(bad_metrics) > 0:
                result.append({'user': user_serialized_data[i],
                               'total_feedbacks_count': user_feedbacks.count(),
                               'bad_feedbacks': FeedbackReadOnlySerializer(bad_feedbacks, many=True).data,
                               'bad_metrics': EvaluationMetricSerializer(list(bad_metrics), many=True).data,
                               'average_score': average_sum / user_feedbacks.count()})

        if ordering == 'bad_feedbacks':
            result.sort(key=lambda a: -len(a['bad_feedbacks']))
        elif ordering == 'total_feedbacks':
            result.sort(key=lambda a: -a['total_feedbacks_count'])
        elif ordering == 'ratio':
            result.sort(key=lambda a: -len(a['bad_feedbacks'])/a['total_feedbacks_count'])
        else:
            result.sort(key=lambda a: a['average_score'])

        return JsonResponse(result, safe=False)
