import json

from django.http import JsonResponse
from core.models import RequestCatalogue

# Create your views here.
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.models import User
from feedback.models import SystemFeedbackCatalogue, SystemFeedback, EvaluationMetricCatalogue, EvaluationMetric, \
    FeedbackCatalogue, Feedback
from feedback.serializers import SystemFeedbackSerializer, SystemFeedbackReplySerializer, EvaluationMetricSerializer, \
    FeedbackSerializer
from utils.helper_funcs import ListAdapter
from utils.permissions import PermissionFactory


class EvaluationMetricView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.CompanyManager).get_permission_class()]

    def get(self, request, evaluation_metric_id='', *args, **kwargs):
        eval_metric = None
        if evaluation_metric_id:
            ids = [int(evaluation_metric_id)]
            eval_metric = EvaluationMetricCatalogue().search(query={'id': ids})
            if not eval_metric:
                return JsonResponse({'error': 'No evaluation metric found'}, status=HTTP_404_NOT_FOUND)
        else:
            try:
                query = json.loads(request.GET.get('q'))
            except:
                query = {}
            eval_metric = EvaluationMetricCatalogue().search(query=query)

        serializer = EvaluationMetricSerializer(eval_metric, many=True)

        return JsonResponse(serializer.data, safe=False)

    def post(self, request, *args, **kwargs):
        serializer = EvaluationMetricSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)

    def delete(self, request, evaluation_metric_id='', *args, **kwargs):
        if evaluation_metric_id:
            ids = [int(evaluation_metric_id)]
        else:
            ids = request.data.get("id")
        if not ids:
            return JsonResponse({'error': 'No id provided'}, status=HTTP_400_BAD_REQUEST)
        id_list = ListAdapter().python_ensure_list(ids)
        eval_metrics = EvaluationMetricCatalogue().search({'id': id_list})
        if not eval_metrics:
            return JsonResponse({'error': 'No evaluation metric found'}, status=HTTP_404_NOT_FOUND)
        output_ids = list(map(lambda x: x.id, eval_metrics))
        eval_metrics.delete()
        return JsonResponse({'ids': output_ids})

    def put(self, request, evaluation_metric_id='', *args, **kwargs):
        if not evaluation_metric_id:
            return JsonResponse({'error': 'No id provided'}, status=HTTP_400_BAD_REQUEST)
        try:
            eval_metric = EvaluationMetricCatalogue().search(query={'id': evaluation_metric_id}).first()
        except:
            return JsonResponse({'error': 'No evaluation metric found'}, status=HTTP_404_NOT_FOUND)
        serializer = EvaluationMetricSerializer(eval_metric, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)


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

    def get(self, request, service_request_id=None):
        if service_request_id:
            feedback = FeedbackCatalogue().serach_by_request(service_request_id, request.user.id)
            if not feedback:
                return JsonResponse({'error': 'Feedback not found'}, status=HTTP_404_NOT_FOUND)

            serialized = FeedbackSerializer(feedback)
            return JsonResponse(serialized.data, safe=False)

    def post(self, request, service_request_id):
        service_request = RequestCatalogue().search(query={'id': service_request_id})
        if not service_request:
            return JsonResponse({'error': 'Request not found'}, status=HTTP_404_NOT_FOUND)

        service_request = request.first()

        print("FeedbackView post", service_request)

        pass
