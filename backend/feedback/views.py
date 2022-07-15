import json

from django.http import JsonResponse
# Create your views here.
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import User
from feedback.models import SystemFeedbackCatalogue
from feedback.serializers import SystemFeedbackSerializer
from utils.permissions import PermissionFactory


class SubmitSystemFeeedbackView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Customer).get_permission_class() | PermissionFactory(
        User.UserRole.Specialist).get_permission_class()]

    def post(self, request, *args, **kwargs):
        data = {
            'user': request.user.id,
            'text': request.data['text']
        }
        serializer = SystemFeedbackSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)


class SearchSystemFeeedbackView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.GET)
        system_feedback = SystemFeedbackCatalogue().search(json.loads(request.GET.get('q')))
        serialized = SystemFeedbackSerializer(system_feedback, many=True)
        return JsonResponse(serialized.data, safe=False)
