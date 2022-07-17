import json

from django.http import JsonResponse
from knox.auth import TokenAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.models import Request, Location
from core.serializers import RequestSerializer, LocationSerializer


# Create your views here.


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
