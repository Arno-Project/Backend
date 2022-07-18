import json

from django.http import JsonResponse
from knox.auth import TokenAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import User
from core.models import Request, Location
from core.serializers import RequestSerializer, LocationSerializer, RequestSubmitSerializer

# Create your views here.
from utils.permissions import PermissionFactory


class RequestSearchView(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.GET)
        requests = Request.search(json.loads(request.GET.get('q')))
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
        # TODO Use Catalogue :|
        for field in ['location', 'description']:
            if field in request.data:
                data[field] = request.data[field]
        data['desired_start_time'] = request.data['desired_start_time']
        data['requested_speciality'] = request.data['requested_speciality']
        serializer = RequestSubmitSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        request = serializer.save()
        return JsonResponse({
            'request': RequestSerializer(request).data
        })
