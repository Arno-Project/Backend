import json

from django.http import JsonResponse
from rest_framework.response import Response
from rest_condition import And, Or, Not
from .serializers import MetricScoreSerializer, ScorePolicySerializer
from .models import EvaluationMetric, MetricScore, ScoreCalculator, ScorePolicy
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from accounts.models import User, NormalUser
from core.models import RequestCatalogue
from feedback.models import SystemFeedbackCatalogue, SystemFeedback, EvaluationMetricCatalogue, FeedbackCatalogue
from feedback.serializers import SystemFeedbackSerializer, SystemFeedbackReplySerializer, EvaluationMetricSerializer, \
    FeedbackSerializer, FeedbackReadOnlySerializer
from log.models import Logger
from utils.helper_funcs import ListAdapter
from utils.permissions import PermissionFactory, IsReadyOnlyRequest
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
        if request.user.get_role() == User.UserRole.Customer:
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
    permission_classes = [Or(PermissionFactory(User.UserRole.Specialist).get_permission_class(),
                             PermissionFactory(User.UserRole.Customer).get_permission_class(),
                             And(IsReadyOnlyRequest,
                                 PermissionFactory(User.UserRole.TechnicalManager).get_permission_class()
                                 ),
                             And(IsReadyOnlyRequest,
                                 PermissionFactory(User.UserRole.CompanyManager).get_permission_class()
                                 )
                             )]

    @Logger().log_name()
    def get(self, request):
        service_request_id = request.GET.get('request_id', None)

        if service_request_id:
            print("req id", service_request_id)
            feedback = FeedbackCatalogue().search_by_request(
                service_request_id, request.user.id)
            if not feedback:
                return JsonResponse({'error': FEEDBACK_NOT_FOUND_ERROR}, status=HTTP_404_NOT_FOUND)

            print(feedback)
            serialized = FeedbackReadOnlySerializer(feedback, many=True)
            return JsonResponse(serialized.data, safe=False)

        feedbacks = FeedbackCatalogue().get_feedback_list()
        serialized = FeedbackReadOnlySerializer(feedbacks, many=True)
        return JsonResponse(serialized.data, safe=False)

    @Logger().log_name()
    def post(self, request):
        request_id = request.data.get('request_id', -1)
        metric_scores = request.data.get('metric_scores', [])
        description = request.data.get('description', '')

        query = {'id': request_id}
        eval_metric_query = {}

        if request.user.get_role() == User.UserRole.Specialist:
            query['specialist'] = {'id': request.user.id}
            eval_metric_query['user_type'] = 'C'
        else:
            query['customer'] = {'id': request.user.id}
            eval_metric_query['user_type'] = 'S'

        service_request = RequestCatalogue().search(query)

        old_feedbacks = FeedbackCatalogue().search_by_request(request_id, request.user.id)

        if not service_request:
            return JsonResponse({'error': REQUEST_NOT_FOUND_ERROR}, status=HTTP_404_NOT_FOUND)

        eval_metrics = EvaluationMetricCatalogue().search(query=eval_metric_query)

        metric_scores_data = []
        for metric_score_dict in metric_scores:
            try:
                metric = eval_metrics.get(
                    pk=int(metric_score_dict['metric_id']))
            except EvaluationMetric.DoesNotExist:
                return JsonResponse({'error': NO_EVALUATION_METRIC_FOUND_ERROR}, status=HTTP_400_BAD_REQUEST)

            data = {
                'metric': int(metric_score_dict['metric_id']),
                'score': metric_score_dict.get('rating', 50),
            }

            serializer = MetricScoreSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            metric_score = serializer.save()
            metric_scores_data.append(metric_score.pk)

        data = {
            'metric_scores': metric_scores_data,
            'request': request_id,
            'user': NormalUser.objects.get(user__pk=request.user.id).pk,
            'description': description
        }

        if old_feedbacks:
            print("old_feedback", old_feedbacks)
            for f in old_feedbacks:  # dont use bulk delete
                f.delete()

        serializer = FeedbackSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        feedback = serializer.save()

        return JsonResponse(serializer.data)


class ForceUpdateScoresView(APIView):
    # TODO Class diagram
    authentication_classes = [TokenAuthentication]
    permission_classes = [PermissionFactory(User.UserRole.TechnicalManager).get_permission_class() |
                          PermissionFactory(User.UserRole.CompanyManager).get_permission_class()]

    @Logger().log_name()
    def post(self, request, user_id=''):
        if user_id == '':
            users = NormalUser.objects.all()
        else:
            users = NormalUser.objects.filter(pk=user_id)
        for user in users:
            ScoreCalculator(user).update_score()

        return JsonResponse({'success': True})


class ScorePolicyView(APIView):
    # TODO Class diagram
    authentication_classes = [TokenAuthentication]
    permission_classes = [Or(PermissionFactory(User.UserRole.TechnicalManager).get_permission_class(),
                             PermissionFactory(User.UserRole.CompanyManager).get_permission_class(),
                             And(IsReadyOnlyRequest,
                                 PermissionFactory(User.UserRole.Specialist).get_permission_class()))
                          ]

    @Logger().log_name()
    def get(self, request, score_policy_id=''):
        many = True
        if score_policy_id != '':
            try:
                score_policy = ScorePolicy.objects.get(pk=score_policy_id)
            except ScorePolicy.DoesNotExist:
                return JsonResponse({'error': SCORE_POLICY_NOT_FOUND_ERROR}, status=HTTP_404_NOT_FOUND)
            many = False
        else:
            score_policy = ScorePolicy.objects.all()
        serialized = ScorePolicySerializer(score_policy, many=many)
        return JsonResponse(serialized.data, safe=False)

    @Logger().log_name()
    def post(self, request, score_policy_id=''):
        data = {
            'minimum_score': request.data.get('minimum_score', 0),
            'allowed_requests': request.data.get('allowed_requests', 0),
        }

        serializer = ScorePolicySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)

    @Logger().log_name()
    def put(self, request, score_policy_id=''):
        try:
            score_policy = ScorePolicy.objects.get(pk=score_policy_id)
        except ScorePolicy.DoesNotExist:
            return JsonResponse({'error': SCORE_POLICY_NOT_FOUND_ERROR}, status=HTTP_404_NOT_FOUND)

        data = {
            'minimum_score': request.data.get('minimum_score', score_policy.get_minimum_score()),
            'allowed_requests': request.data.get('allowed_requests', score_policy.get_allowed_requests()),
        }

        serializer = ScorePolicySerializer(score_policy, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data)

    @Logger().log_name()
    def delete(self, request, score_policy_id=''):
        try:
            score_policy = ScorePolicy.objects.get(pk=score_policy_id)
        except ScorePolicy.DoesNotExist:
            return JsonResponse({'error': SCORE_POLICY_NOT_FOUND_ERROR}, status=HTTP_404_NOT_FOUND)
        score_policy.delete()
        return JsonResponse({})
