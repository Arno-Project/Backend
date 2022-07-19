import json

from django.http import JsonResponse
# Create your views here.
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import User
from feedback.models import SystemFeedbackCatalogue, SystemFeedback
from feedback.serializers import SystemFeedbackSerializer, SystemFeedbackReplySerializer
from utils.permissions import PermissionFactory


class SubmitSystemFeedbackView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Customer).get_permission_class() | PermissionFactory(
        User.UserRole.Specialist).get_permission_class()]

    def post(self, request, *args, **kwargs):
        data = {
            'user': request.user.normal_user_user.id,
            'text': request.data['text'],
            'type': request.data.get('type', "O")
        }
        serializer = SystemFeedbackSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)


class SearchSystemFeedbackView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.GET)
        system_feedback = SystemFeedbackCatalogue().search(json.loads(request.GET.get('q')))
        serialized = SystemFeedbackSerializer(system_feedback, many=True)
        return JsonResponse(serialized.data, safe=False)


class SubmitSystemFeedbackReplyView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.TechnicalManager).get_permission_class()]

    def post(self, request, *args, **kwargs):
        system_feedback_id = request.data['system_feedback']
        system_feedback: SystemFeedback = SystemFeedback.objects.get(pk=system_feedback_id)
        data = {
            'user': request.user.manager_user_user.technical_manager_user.id,
            'text': request.data['text'],

        }
        serializer = SystemFeedbackReplySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        reply = serializer.save()
        system_feedback.set_reply(reply)
        system_feedback.save(force_update=True)
        return JsonResponse(serializer.data)
