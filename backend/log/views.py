import json

from django.http import JsonResponse
# Create your views here.
from knox.auth import TokenAuthentication
from rest_framework import generics

from accounts.models import User
from log.models import LogCatalogue
from log.serializers import LogSerializer
from utils.permissions import PermissionFactory


class LogSearchView(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.TechnicalManager).get_permission_class() | PermissionFactory(
        User.UserRole.CompanyManager).get_permission_class()]

    def get(self, request):
        query = json.loads(request.GET.get('q'))
        requests = LogCatalogue().search(query)
        serialized = LogSerializer(requests, many=True)
        return JsonResponse(serialized.data, safe=False)
