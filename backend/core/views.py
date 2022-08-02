import json

from django.http import JsonResponse
from knox.auth import TokenAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from accounts.models import User, UserCatalogue, Specialist
from core.models import Request, Location, RequestCatalogue
from core.serializers import RequestSerializer, LocationSerializer, RequestSubmitSerializer
from django.utils.translation import gettext_lazy as _

# Create your views here.
from notification.notifications import RequestInitialAcceptBySpecialistNotification, \
    RequestAcceptanceFinalizeByCustomerNotification, RequestRejectFinalizeByCustomerNotification, BaseNotification, \
    SelectSpecialistForRequestNotification, RequestAcceptanceFinalizeBySpecialistNotification, \
    RequestRejectFinalizeBySpecialistNotification
from utils.permissions import PermissionFactory


class RequestSearchView(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = json.loads(request.GET.get('q'))
        if request.user.role == User.UserRole.Customer:
            query['customer'] = {}
            query['customer']['id'] = request.user.id
        if request.user.role == User.UserRole.Specialist:
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
            query={'requested_speciality': requested_speciality, 'customer': {'id': request.user.id}})
        if _request.exists():
            print("here")
            return Response({
                'error': _('You have already requested this speciality')
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


class RequestCancelByManagerView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.CompanyManager).get_permission_class() | PermissionFactory(
        User.UserRole.TechnicalManager).get_permission_class()]

    def post(self, request):
        request_id = request.data.get('request_id')
        request = Request.objects.get(pk=request_id)
        if request.get_status() == Request.RequestStatus.CANCELED:
            return Response({
                'error': _('Request already canceled')
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
                'error': _('Request not found')
            }, status=HTTP_404_NOT_FOUND)

        if request is None:
            return Response({
                'error': _('Request not found')
            }, status=HTTP_404_NOT_FOUND)
        if request.get_status() == Request.RequestStatus.WAITING_FOR_SPECIALIST_ACCEPTANCE_FROM_CUSTOMER:
            return Response({
                'error': _('request already in initial acceptance status from specialist')
            }, status=HTTP_400_BAD_REQUEST)
        if request.get_status() != Request.RequestStatus.PENDING:
            return Response({
                'error': _('Request is not in pending status')
            }, status=HTTP_400_BAD_REQUEST)

        if request.get_requested_speciality() not in user.full_user.get_speciality():
            return Response({
                'error': _('You does not have required speciality')
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


class RequestAcceptanceFinalizeByCustomerView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Customer).get_permission_class()]

    notification_builder_accept: BaseNotification = RequestAcceptanceFinalizeByCustomerNotification
    notification_builder_reject: BaseNotification = RequestRejectFinalizeByCustomerNotification

    def validate(self, request, customer):
        try:
            request = request.first()
        except:
            return Response({
                'error': _('Request not found')
            }, status=HTTP_404_NOT_FOUND)

        if request is None:
            return Response({
                'error': _('Request not found')
            }, status=HTTP_404_NOT_FOUND)
        if request.customer != customer:
            return Response({
                'error': _('Request is not for you')
            }, status=HTTP_400_BAD_REQUEST)
        if request.get_status() != Request.RequestStatus.WAITING_FOR_SPECIALIST_ACCEPTANCE_FROM_CUSTOMER:
            return Response({
                'error': _('Request is not in waiting for customer acceptance from specialist status')
            }, status=HTTP_400_BAD_REQUEST)

        return None

    def post(self, request):
        request_id = request.data.get('request_id')
        if request_id is None:
            return Response({
                'error': _('request_id is required')
            }, status=HTTP_400_BAD_REQUEST)
        core_request = RequestCatalogue().search(query={"id": request_id})
        if result := self.validate(core_request, request.user.full_user):
            return result
        core_request = core_request.first()

        is_accept = request.data.get('is_accept')
        if is_accept is None:
            return Response({
                'error': _('is_accept is required')
            }, status=HTTP_400_BAD_REQUEST)
        # TODO, More OOP Refactor
        if is_accept == "1":
            core_request.set_status(Request.RequestStatus.IN_PROGRESS)
            self.notification_builder_reject(core_request).build()
        else:
            core_request.set_status(Request.RequestStatus.PENDING)
            core_request.set_specialist(None)
            self.notification_builder_accept(core_request).build()

        core_request.save()
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
                'error': _('Request not found')
            }, status=HTTP_404_NOT_FOUND)
        try:
            specialist = specialist.first()
        except:
            return Response({
                'error': _('Specialist not found')
            }, status=HTTP_404_NOT_FOUND)

        if request is None:
            return Response({
                'error': _('Request not found')
            }, status=HTTP_404_NOT_FOUND)
        if request.get_status() != Request.RequestStatus.PENDING:
            return Response({
                'error': _('Request is not in pending status')
            }, status=HTTP_400_BAD_REQUEST)

        if request.get_requested_speciality() not in specialist.full_user.get_speciality():
            return Response({
                'error': _('Selected specialist does not have required speciality')
            }, status=HTTP_400_BAD_REQUEST)
        return None

    def post(self, request):
        request_id = request.data.get('request_id')
        specialist_id = request.data.get('specialist_id')
        if specialist_id is None:
            return Response({
                'error': _('specialist_id is required')
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


class RequestAcceptanceFinalizeBySpecialistView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Specialist).get_permission_class()]

    notification_builder_accept: BaseNotification = RequestAcceptanceFinalizeBySpecialistNotification
    notification_builder_reject: BaseNotification = RequestRejectFinalizeBySpecialistNotification

    def validate(self, request, specialist):
        try:
            request = request.first()
        except:
            return Response({
                'error': _('Request not found')
            }, status=HTTP_404_NOT_FOUND)

        if request is None:
            return Response({
                'error': _('Request not found')
            }, status=HTTP_404_NOT_FOUND)
        if request.get_specialist() != specialist.full_user:
            return Response({
                'error': _('Request is not for you')
            }, status=HTTP_400_BAD_REQUEST)
        if request.get_status() != Request.RequestStatus.WAITING_FOR_CUSTOMER_ACCEPTANCE_FROM_SPECIALIST:
            return Response({
                'error': _('Request is not in waiting for customer acceptance from specialist status')
            }, status=HTTP_400_BAD_REQUEST)

        return None

    def post(self, request):
        request_id = request.data.get('request_id')
        core_request = RequestCatalogue().search(query={"id": request_id})
        if result := self.validate(core_request, request.user):
            return result
        core_request = core_request.first()

        is_accept = request.data.get('is_accept')
        if is_accept is None:
            return Response({
                'error': _('is_accept is required')
            }, status=HTTP_400_BAD_REQUEST)
        # TODO, More OOP Refactor
        if is_accept == "1":
            core_request.set_status(Request.RequestStatus.IN_PROGRESS)
            self.notification_builder_reject(core_request).build()
        else:
            core_request.set_status(Request.RequestStatus.PENDING)
            core_request.set_specialist(None)
            self.notification_builder_accept(core_request).build()
        core_request.save()
        return JsonResponse({
            'request': RequestSerializer(core_request).data
        })


class RequestStatusView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Customer).get_permission_class() | PermissionFactory(
        User.UserRole.Specialist).get_permission_class()]

    def get(self, request):
        if request.user.role == User.UserRole.Customer:
            requests = Request.objects.filter(customer=request.user.full_user)
        elif request.user.role == User.UserRole.Specialist:
            requests = Request.objects.filter(specialist=request.user.full_user)
        else:
            return Response(data=_('You are not a customer or a specialist'), status=HTTP_400_BAD_REQUEST)
        serialized = RequestSerializer(requests, many=True)
        return JsonResponse({
            'requests': serialized.data
        })
