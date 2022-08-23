import sys
from typing import List

from django.db import models

from django.db.models import Q

import accounts.models
from accounts.models import NormalUser
from arno.settings import USE_SCORE_LIMIT
from core.models import Request
from utils.Singleton import Singleton

from django.utils.translation import gettext_lazy as _
from utils.helper_funcs import ListAdapter


class EvaluationMetric(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    user_type = models.CharField(max_length=2, choices=accounts.models.User.UserRole.choices,
                                 default=accounts.models.User.UserRole.Customer)

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def get_user_role(self):
        return self.user_type

    def set_title(self, title):
        self.title = title

    def set_description(self, description):
        self.description = description

    def set_user_role(self, user_role):
        self.user_type = user_role


class EvaluationMetricCatalogue(metaclass=Singleton):
    @property
    def metrics(self):
        return EvaluationMetric.objects.all()

    def search(self, query):
        result = self.metrics
        print(query)

        if not query:
            return result
        for field in ['id']:
            if query.get(field):
                result = result.filter(
                    pk__in=ListAdapter().python_ensure_list(query[field]))
        for field in ['title', 'description']:
            if query.get(field):
                result = result.filter(
                    Q(**{field + '__icontains': query[field]}))
        if query.get('user_type'):
            print(query.get('user_type'))
            result = result.filter(user_type__iexact=query['user_type'])
        # filter User objects that exist in Customer Table
        return result

    def get_evaluation_metric_list(self):
        return self.metrics


class MetricScore(models.Model):
    metric = models.ForeignKey(EvaluationMetric, on_delete=models.CASCADE)
    score = models.IntegerField(null=False, blank=False)

    def get_metric(self):
        return self.metric

    def get_score(self):
        return self.score

    def set_metric(self, metric):
        self.metric = metric

    def set_score(self, score):
        self.score = score


class Feedback(models.Model):
    description = models.TextField(null=False, blank=True)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    metric_scores = models.ManyToManyField(MetricScore, blank=True, null=True)
    user = models.ForeignKey(NormalUser, on_delete=models.CASCADE)

    def get_description(self):
        return self.description

    def get_request(self):
        return self.request

    def get_created_at(self):
        return self.created_at

    def set_created_at(self, created_at):
        self.created_at = created_at

    def get_scores(self):
        return self.metric_scores

    def submit_scores(self, scores: List[MetricScore]):
        pass

    def delete(self, *args, **kwargs):
        print("deleting")
        for s in self.metric_scores.all():
            s.delete()
        return super().delete(*args, **kwargs)

    def get_average_score(self):
        counter = 0
        sum = 0
        for metric_score in self.metric_scores.all():
            sum += metric_score.score
            counter += 1

        return 100 if counter == 0 else sum / counter


class FeedbackCatalogue(metaclass=Singleton):
    @property
    def feedbacks(self):
        return Feedback.objects.all()

    def search(self, query):
        result = self.feedbacks

        if query.get('user'):
            result = result.filter(user__user__id=query['user'])

        if query.get('request'):
            result = result.filter(request__id=query['request'])

        if query.get('after'):
            result = result.filter(created_at__gte=query.get('after'))

        return result


class SystemFeedbackReply(models.Model):
    text = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        accounts.models.TechnicalManager, on_delete=models.CASCADE)

    def get_user(self):
        return self.user

    def get_text(self):
        return self.text

    def set_text(self, text: str):
        self.text = text


class SystemFeedback(models.Model):
    class SystemFeedbackType(models.TextChoices):
        Technical = 'T', _('Technical')
        Complaint = 'C', _('Complaint')
        Suggestion = 'S', _('Suggestion')
        Other = 'O', _('Other')

    class SystemFeedbackStatus(models.TextChoices):
        New = 'N', _('New')
        Viewed = 'V', _('Viewed')
        Replied = 'R', _('Replied')

    text = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        max_length=1, choices=SystemFeedbackType.choices, default=SystemFeedbackType.Other)
    status = models.CharField(
        max_length=1, choices=SystemFeedbackStatus.choices, default=SystemFeedbackStatus.New)
    user = models.ForeignKey(accounts.models.NormalUser,
                             on_delete=models.CASCADE)
    reply = models.ForeignKey(
        SystemFeedbackReply, on_delete=models.CASCADE, null=True, blank=True)

    def get_text(self):
        return self.text

    def set_text(self, text: str):
        self.text = text

    def set_status(self, status):
        self.status = status

    def get_type(self):
        return self.type

    def get_user(self):
        return self.user

    def set_reply(self, reply):
        self.reply = reply
        self.set_status(self.SystemFeedbackStatus.Replied)

    def get_reply(self):
        return self.reply

    class Meta:
        ordering = ['-created_at']


class SystemFeedbackCatalogue(metaclass=Singleton):
    @property
    def feedbacks(self):
        return SystemFeedback.objects.all()

    def search(self, query):
        result = self.feedbacks
        for field in ['type', 'status']:
            if query.get(field):
                result = result.filter(Q(**{field + '__iexact': query[field]}))
        for field in ['-type', '-status']:
            if query.get(field):
                result = result.exclude(
                    Q(**{field[1:] + '__iexact': query[field]}))
        for field in ['user']:
            if query.get(field):
                result = result.filter(Q(**{field + '__iexact': query[field]}))
        for field in ['has_reply']:
            if query.get(field):
                result = result.filter(reply__isnull=not query[field])

        return result


class ScorePolicy(models.Model):
    minimum_score = models.FloatField(null=False, blank=False)
    allowed_requests = models.IntegerField(null=False, blank=False)

    def get_minimum_score(self):
        return self.minimum_score

    def get_allowed_requests(self):
        return self.allowed_requests

    def set_minimum_score(self, minimum_score):
        self.minimum_score = minimum_score

    def set_allowed_requests(self, allowed_requests):
        self.allowed_requests = allowed_requests


class ScoreCalculator:

    def __init__(self, normal_user: NormalUser):
        self.normal_user = normal_user

    def update_score(self):
        print("UPDATE SCORE")
        if self.normal_user.user.get_role() == accounts.models.User.UserRole.Customer:
            requests = Request.objects.filter(
                customer__id=self.normal_user.user.full_user.id)
        elif self.normal_user.user.get_role() == accounts.models.User.UserRole.Specialist:
            requests = Request.objects.filter(
                specialist__id=self.normal_user.user.full_user.id)
        else:
            raise Exception()

        feedbacks = []
        for request in requests:
            feedbacks_ = Feedback.objects.filter(request__id=request.id).exclude(
                user_id=self.normal_user.id)
            feedbacks.extend(feedbacks_)

        counter = 0
        sum = 0
        for feedback in feedbacks:
            for metric_score in feedback.metric_scores.all():
                sum += metric_score.score
                counter += 1

        if counter == 0:
            self.normal_user.set_score(100)
        else:
            self.normal_user.set_score(sum / counter)
        self.normal_user.save()


class ScorePolicyChecker:

    def __init__(self, score):
        self.score = score

    def get_allowed_request(self):
        if not USE_SCORE_LIMIT:
            return 20
        score_policies = ScorePolicy.objects.all().order_by('-minimum_score')
        if not score_policies.exists():
            print("no score policy")
            best_allowed_request = 20
        else:
            print("set to 0")
            best_allowed_request = 0
        for score_policy in score_policies:
            print(score_policy.minimum_score)
            if self.score >= score_policy.minimum_score:
                best_allowed_request = score_policy.allowed_requests
            else:
                break
        print(best_allowed_request)
        return best_allowed_request
