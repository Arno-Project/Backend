import json

from django.http import JsonResponse
from knox.auth import TokenAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from accounts.models import User
from core.models import Request, Location, RequestCatalogue
from core.serializers import RequestSerializer, LocationSerializer, RequestSubmitSerializer
from django.utils.translation import gettext_lazy as _

# Create your views here.
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
            query['speciality']['id'] = request.user.full_user.speciality.all()
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
        data = {'customer': User.objects.get(pk=request.user.id).normal_user_user.customer_normal_user.id}
        requested_speciality = request.data['requested_speciality']
        # TODO Use Catalogue :|
        if Request.objects.filter(customer=request.user.normal_user_user.customer_normal_user,
                                  requested_speciality=requested_speciality).exists():
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
