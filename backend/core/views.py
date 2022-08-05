import datetime
import json
import uuid
from abc import ABC

from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from knox.auth import TokenAuthentication
from rest_framework import generics
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_201_CREATED
from rest_framework.views import APIView

from accounts.models import User, UserCatalogue
from arno.settings import MEDIA_ROOT
from core.constants import *
from core.models import Request, Location, RequestCatalogue
from core.serializers import RequestSerializer, LocationSerializer, RequestSubmitSerializer
from notification.notifications import RequestInitialAcceptBySpecialistNotification, \
    RequestAcceptanceFinalizeByCustomerNotification, RequestRejectFinalizeByCustomerNotification, BaseNotification, \
    SelectSpecialistForRequestNotification, RequestAcceptanceFinalizeBySpecialistNotification, \
    RequestRejectFinalizeBySpecialistNotification
from utils.permissions import PermissionFactory


class FileUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, format=''):
        up_file = request.FILES['file']

        # up file name without extension
        file_name = up_file.name.split('.')[0]
        extension = up_file.name.split('.')[1]
        full_name = file_name + '-' + str(uuid.uuid4()) + '.' + extension
        request.user.full_user.document = up_file
        print("hello")
        with open(MEDIA_ROOT + "/" + full_name, 'wb+') as destination:
            for chunk in up_file.chunks():
                destination.write(chunk)

        return Response(up_file.name, HTTP_201_CREATED)


class RequestSearchView(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = json.loads(request.GET.get('q'))
        if request.user.get_role() == User.UserRole.Customer:
            query['customer'] = {}
            query['customer']['id'] = request.user.id
        if request.user.get_role() == User.UserRole.Specialist:
            query['speciality'] = {}
            query['speciality']['id'] = request.user.full_user.get_speciality()
        requests = RequestCatalogue().search(query)
        serialized = RequestSerializer(requests, many=True)
        return JsonResponse(serialized.data, safe=False)


class LocationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        id_set = set(request.GET.getlist('id'))
        locations = Location.objects.filter(id__in=id_set)
        serialized = LocationSerializer(locations, many=True)
        return JsonResponse({
            'locations': serialized.data
        })

    def post(self, request, *args, **kwargs):
        serializer = LocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        location = serializer.save()
        return JsonResponse({
            'location': LocationSerializer(location).data
        })


class RequestSubmitView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Customer).get_permission_class()]

    def post(self, request, *args, **kwargs):
        data = {'customer': UserCatalogue().search(query={'id': request.user.id, 'role': "C"})[0].full_user.id}
        requested_speciality = request.data['requested_speciality']
        _request = RequestCatalogue().search(
            query={'speciality': requested_speciality, 'customer': {'id': request.user.id}})
        _request = _request \
            .exclude(status__exact=Request.RequestStatus.DONE) \
            .exclude(status__exact=Request.RequestStatus.CANCELED)
        if _request.exists():
            return Response({
                'error': _(YOU_ALREADY_REQUESTED_THIS_SPECIALTY_ERROR)
            }, status=HTTP_400_BAD_REQUEST)

        for field in ['location', 'description']:
            if field in request.data:
                data[field] = request.data[field]
        data['desired_start_time'] = request.data['desired_start_time']
        data['requested_speciality'] = requested_speciality
        serializer = RequestSubmitSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        request = serializer.save()
        return JsonResponse({
            'request': RequestSerializer(request).data
        })


class RequestCancelByCustomerView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Customer).get_permission_class()]

    def post(self, request):
        # TODO Add more checks on status of request
        request_id = request.data.get('request_id')
        _request = RequestCatalogue().search(query={'id': request_id})
        if not _request.exists():
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)
        _request = _request[0]
        if _request.customer != request.user.full_user:
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)
        if _request.status == Request.RequestStatus.DONE:
            return Response({
                'error': _(REQUEST_ALREADY_DONE_ERROR)
            }, status=HTTP_400_BAD_REQUEST)
        if _request.get_status() == Request.RequestStatus.CANCELED:
            return Response({
                'error': _(REQUEST_ALREADY_CANCELLED_ERROR)
            }, status=HTTP_400_BAD_REQUEST)

        _request.cancel()
        return JsonResponse({
            'request': RequestSerializer(_request).data
        })


class RequestCancelByManagerView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.CompanyManager).get_permission_class() | PermissionFactory(
        User.UserRole.TechnicalManager).get_permission_class()]

    def post(self, request):
        request_id = request.data.get('request_id')
        request = RequestCatalogue().search(query={'id': request_id})
        if not request.exists():
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)
        request = request[0]
        if request.get_status() == Request.RequestStatus.CANCELED:
            return Response({
                'error': _(REQUEST_ALREADY_CANCELLED_ERROR)
            }, status=HTTP_400_BAD_REQUEST)

        request.cancel()
        return JsonResponse({
            'request': RequestSerializer(request).data
        })


class RequestInitialAcceptBySpecialistView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Specialist).get_permission_class()]
    notification_builder: BaseNotification = RequestInitialAcceptBySpecialistNotification

    def validate(self, request, user):
        try:
            request = request.first()
        except:
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)

        if request is None:
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)
        if request.get_status() == Request.RequestStatus.WAITING_FOR_SPECIALIST_ACCEPTANCE_FROM_CUSTOMER:
            return Response({
                'error': _(REQUEST_ALREADY_IN_INITIAL_ACCEPTANCE_STATUS_ERROR)
            }, status=HTTP_400_BAD_REQUEST)
        # TODO DUPLICATE
        if request.get_status() != Request.RequestStatus.PENDING:
            return Response({
                'error': _(REQUEST_NOT_IN_PENDING_ERROR)
            }, status=HTTP_400_BAD_REQUEST)

        if request.get_requested_speciality() not in user.full_user.get_speciality():
            return Response({
                'error': _(YOU_DONT_HAVE_SPECIALITY_ERROR)
            }, status=HTTP_400_BAD_REQUEST)
        return None

    def post(self, request):
        request_id = request.data.get('request_id')
        core_request = RequestCatalogue().search(query={"id": request_id})
        if result := self.validate(core_request, request.user):
            return result
        core_request = core_request.first()

        # TODO, More OOP Refactor
        core_request.set_status(Request.RequestStatus.WAITING_FOR_SPECIALIST_ACCEPTANCE_FROM_CUSTOMER)
        core_request.set_specialist(request.user.full_user)
        core_request.save()

        self.notification_builder(core_request).build()

        return JsonResponse({
            'request': RequestSerializer(core_request).data
        })


class SelectSpecialistForRequestView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Customer).get_permission_class()]
    notification_builder: BaseNotification = SelectSpecialistForRequestNotification

    def validate(self, request, specialist):
        try:
            request = request.first()
        except:
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)
        try:
            specialist = specialist.first()
        except:
            return Response({
                'error': _(SPECIALIST_NOT_FOUND)
            }, status=HTTP_404_NOT_FOUND)

        if request is None:
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)
        if request.get_status() != Request.RequestStatus.PENDING:
            return Response({
                'error': _(REQUEST_NOT_IN_PENDING_ERROR)
            }, status=HTTP_400_BAD_REQUEST)

        if request.get_requested_speciality() not in specialist.full_user.get_speciality():
            return Response({
                'error': _(SPECIALIST_DONT_HAVE_SPECIALITY_ERROR)
            }, status=HTTP_400_BAD_REQUEST)
        return None

    def post(self, request):
        request_id = request.data.get('request_id')
        specialist_id = request.data.get('specialist_id')
        if specialist_id is None:
            return Response({
                'error': _(SPECIALIST_ID_REQUIRED_ERROR)
            }, status=HTTP_400_BAD_REQUEST)
        core_request = RequestCatalogue().search(query={"id": request_id})
        specialist = UserCatalogue().search(query={"specialist_id": specialist_id})

        if result := self.validate(core_request, specialist):
            return result
        core_request = core_request.first()
        specialist = specialist.first().full_user

        # TODO, More OOP Refactor
        core_request.set_status(Request.RequestStatus.WAITING_FOR_CUSTOMER_ACCEPTANCE_FROM_SPECIALIST)
        core_request.set_specialist(specialist)
        core_request.save()
        self.notification_builder(core_request).build()
        return JsonResponse({
            'request ': RequestSerializer(core_request).data
        })


class RequestAcceptanceFinalizeView(APIView, ABC):
    notification_builder_accept = None
    notification_builder_reject = None

    def __init__(self, notification_builder_accept, notification_builder_reject, **kwargs):
        super().__init__(**kwargs)
        self.notification_builder_accept = notification_builder_accept
        self.notification_builder_reject = notification_builder_reject

    def validate(self, r, c):
        pass

    def post(self, request):
        request_id = request.data.get('request_id')
        if request_id is None:
            return Response({
                'error': _(REQUEST_ID_REQUIRED_ERROR)
            }, status=HTTP_400_BAD_REQUEST)
        core_request = RequestCatalogue().search(query={"id": request_id})
        if result := self.validate(core_request, request.user.full_user):
            return result

        core_request = core_request.first()

        is_accept = request.data.get('is_accept')
        if is_accept is None:
            return Response({
                'error': _(IS_ACCEPT_REQUIRED_ERROR)
            }, status=HTTP_400_BAD_REQUEST)
        # TODO, More OOP Refactor
        if is_accept == "1":
            core_request.set_status(Request.RequestStatus.IN_PROGRESS)
            self.notification_builder_accept(core_request).build()
        else:
            core_request.set_status(Request.RequestStatus.PENDING)
            core_request.set_specialist(None)
            core_request.set_accepted_at(datetime.datetime.now())  # TODO check timezone
            self.notification_builder_reject(core_request).build()

        core_request.save()
        return JsonResponse({
            'request': RequestSerializer(core_request).data
        })


class RequestAcceptanceFinalizeByCustomerView(RequestAcceptanceFinalizeView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Customer).get_permission_class()]

    def __init__(self):
        super().__init__(notification_builder_accept=RequestAcceptanceFinalizeByCustomerNotification,
                         notification_builder_reject=RequestRejectFinalizeByCustomerNotification)

    def validate(self, request, customer):
        try:
            request = request.first()
        except:
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)

        if request is None:
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)
        if request.customer != customer:
            return Response({
                'error': _(REQUEST_NOT_FOR_YOU_ERROR)
            }, status=HTTP_400_BAD_REQUEST)
        if request.get_status() != Request.RequestStatus.WAITING_FOR_SPECIALIST_ACCEPTANCE_FROM_CUSTOMER:
            return Response({
                'error': _(REQUEST_NOT_IN_WAITING_FOR_SPECIALIST_ACCEPTANCE_FROM_CUSTOMER_ERROR)
            }, status=HTTP_400_BAD_REQUEST)

        return None


class RequestAcceptanceFinalizeBySpecialistView(RequestAcceptanceFinalizeView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Specialist).get_permission_class()]

    def __init__(self):
        super().__init__(notification_builder_accept=RequestAcceptanceFinalizeBySpecialistNotification,
                         notification_builder_reject=RequestRejectFinalizeBySpecialistNotification)

    def validate(self, request, specialist):
        try:
            request = request.first()
        except:
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)

        if request is None:
            return Response({
                'error': _(REQUEST_NOT_FOUND_ERROR)
            }, status=HTTP_404_NOT_FOUND)
        if request.get_specialist() != specialist:
            return Response({
                'error': _(REQUEST_NOT_FOR_YOU_ERROR)
            }, status=HTTP_400_BAD_REQUEST)
        if request.get_status() != Request.RequestStatus.WAITING_FOR_CUSTOMER_ACCEPTANCE_FROM_SPECIALIST:
            return Response({
                'error': _(REQUEST_NOT_IN_WAITING_FOR_CUSTOMER_ACCEPTANCE_FROM_SPECIALIST_ERROR)
            }, status=HTTP_400_BAD_REQUEST)

        return None


class RequestStatusView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Customer).get_permission_class() | PermissionFactory(
        User.UserRole.Specialist).get_permission_class()]

    def get(self, request):
        if request.user.get_role() == User.UserRole.Customer:
            requests = Request.objects.filter(customer=request.user.full_user)
        elif request.user.get_role() == User.UserRole.Specialist:
            requests = Request.objects.filter(specialist=request.user.full_user)
        else:
            return Response(data=_(NOT_CUSTOMER_OR_SPECIALIST_ERROR), status=HTTP_400_BAD_REQUEST)
        serialized = RequestSerializer(requests, many=True)
        return JsonResponse({
            'requests': serialized.data
        })
