import json

from django.http import JsonResponse
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN
from rest_framework.views import APIView

from accounts.models import User
from core.models import RequestCatalogue
from feedback.models import SystemFeedbackCatalogue, SystemFeedback, EvaluationMetricCatalogue, FeedbackCatalogue
from feedback.serializers import SystemFeedbackSerializer, SystemFeedbackReplySerializer, EvaluationMetricSerializer, \
    FeedbackSerializer
from log.models import Logger
from utils.helper_funcs import ListAdapter
from utils.permissions import PermissionFactory
from feedback.constants import *


class EvaluationMetricView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.CompanyManager).get_permission_class() |
                          PermissionFactory(User.UserRole.Specialist).get_permission_class() |
                          PermissionFactory(User.UserRole.Customer).get_permission_class()]

    @Logger().log_name()
    def get(self, request, evaluation_metric_id='', *args, **kwargs):
        try:
            query = json.loads(request.GET.get('q'))
        except:
            query = {}

        if request.user.get_role() == User.UserRole.Specialist:
            query['user_type'] = 'C'
        if request.user.get_role() == User.UserRole.Specialist:
            query['user_type'] = 'S'

        if evaluation_metric_id:
            ids = [int(evaluation_metric_id)]
            query['id'] = ids
        
        eval_metrics = EvaluationMetricCatalogue().search(query=query)

        if not eval_metrics:
                return JsonResponse({'error': NO_EVALUATION_METRIC_FOUND_ERROR}, status=HTTP_404_NOT_FOUND)

        serializer = EvaluationMetricSerializer(eval_metrics, many=True)

        return JsonResponse(serializer.data, safe=False)

    @Logger().log_name()
    def post(self, request, *args, **kwargs):
        if request.user.get_role() != User.UserRole.CompanyManager:
            return JsonResponse({'error': 'forbidden'}, status=HTTP_403_FORBIDDEN)

        serializer = EvaluationMetricSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)

    @Logger().log_name()
    def delete(self, request, evaluation_metric_id='', *args, **kwargs):
        if request.user.get_role() != User.UserRole.CompanyManager:
            return JsonResponse({'error': 'forbidden'}, status=HTTP_403_FORBIDDEN)

        if evaluation_metric_id:
            ids = [int(evaluation_metric_id)]
        else:
            ids = request.data.get("id")
        if not ids:
            return JsonResponse({'error': NO_ID_PROVIDED_ERROR}, status=HTTP_400_BAD_REQUEST)
        id_list = ListAdapter().python_ensure_list(ids)
        eval_metrics = EvaluationMetricCatalogue().search({'id': id_list})
        if not eval_metrics:
            return JsonResponse({'error': NO_EVALUATION_METRIC_FOUND_ERROR}, status=HTTP_404_NOT_FOUND)
        output_ids = list(map(lambda x: x.id, eval_metrics))
        eval_metrics.delete()
        return JsonResponse({'ids': output_ids})

    @Logger().log_name()
    def put(self, request, evaluation_metric_id='', *args, **kwargs):
        if request.user.get_role() != User.UserRole.CompanyManager:
            return JsonResponse({'error': 'forbidden'}, status=HTTP_403_FORBIDDEN)

        if not evaluation_metric_id:
            return JsonResponse({'error': NO_ID_PROVIDED_ERROR}, status=HTTP_400_BAD_REQUEST)
        try:
            eval_metric = EvaluationMetricCatalogue().search(
                query={'id': evaluation_metric_id}).first()
        except:
            return JsonResponse({'error': NO_EVALUATION_METRIC_FOUND_ERROR}, status=HTTP_404_NOT_FOUND)
        serializer = EvaluationMetricSerializer(eval_metric, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)


class SubmitSystemFeedbackView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.Customer).get_permission_class() | PermissionFactory(
        User.UserRole.Specialist).get_permission_class()]

    @Logger().log_name()
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

    @Logger().log_name()
    def get(self, request):
        print(request.GET)
        system_feedback = SystemFeedbackCatalogue().search(
            json.loads(request.GET.get('q')))
        serialized = SystemFeedbackSerializer(system_feedback, many=True)
        return JsonResponse(serialized.data, safe=False)


class SubmitSystemFeedbackReplyView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(
        User.UserRole.TechnicalManager).get_permission_class()]

    @Logger().log_name()
    def post(self, request, *args, **kwargs):
        system_feedback_id = request.data['system_feedback']
        system_feedback: SystemFeedback = SystemFeedback.objects.get(
            pk=system_feedback_id)
        data = {
            'user': request.user.full_user.id,
            'text': request.data['text'],

        }
        serializer = SystemFeedbackReplySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        reply = serializer.save()
        system_feedback.set_reply(reply)
        system_feedback.save(force_update=True)
        return JsonResponse(serializer.data)


class FeedbackView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @Logger().log_name()
    def get(self, request, service_request_id=None):
        if service_request_id:
            feedback = FeedbackCatalogue().serach_by_request(
                service_request_id, request.user.id)
            if not feedback:
                return JsonResponse({'error': FEEDBACK_NOT_FOUND_ERROR}, status=HTTP_404_NOT_FOUND)

            serialized = FeedbackSerializer(feedback)
            return JsonResponse(serialized.data, safe=False)

    @Logger().log_name()
    def post(self, request, service_request_id):
        service_request = RequestCatalogue().search(
            query={'id': service_request_id})
        if not service_request:
            return JsonResponse({'error': REQUEST_NOT_FOUND_ERROR}, status=HTTP_404_NOT_FOUND)

        service_request = request.first()

        print("FeedbackView post", service_request)

        pass
