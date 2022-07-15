from typing import List

from django.db import models

# Create your models here.
import accounts.models
from core.models import Request
from utils.Singleton import Singleton
from django.utils.translation import gettext_lazy as _


class EvaluationMetric(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    user_type = models.CharField(max_length=2, choices=accounts.models.User.UserRole.choices,
                                 default=accounts.models.User.UserRole.choices)

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


class EvaluationMetricCatalogue(Singleton):
    metrics = EvaluationMetric.objects.all()

    def get_evaluation_metric_list(self):
        return self.metrics

    def search_by_title(self, title: str):
        return self.metrics.filter(title__icontains=title)

    def search_by_user_type(self, user_type):
        return self.metrics.filter(user_type__icontains=user_type)


class MetricScore(models.Model):
    metric = models.ForeignKey(EvaluationMetric, on_delete=models.CASCADE)
    score = models.IntegerField(null=False, blank=False)
    user = models.ForeignKey(accounts.models.User, on_delete=models.CASCADE)

    def get_metric(self):
        return self.metric

    def get_score(self):
        return self.score

    def set_metric(self, metric):
        self.metric = metric

    def set_score(self, score):
        self.score = score


class Feedback(models.Model):
    description = models.TextField(null=False, blank=False)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    metric_scores = models.ManyToManyField(MetricScore, blank=True, null=True)

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


class FeedbackCatalogue(Singleton):
    feedbacks = Feedback.objects.all()

    def get_feedback_list(self):
        return self.feedbacks

    def serach_by_request(self, request):
        pass

    def search_after_time(self, time):
        pass

    def sort_by_time(self, ascending=True):
        pass


class SystemFeedbackReply(models.Model):
    text = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(accounts.models.TechnicalManager, on_delete=models.CASCADE)

    def get_user(self):
        return self.user

    def get_text(self):
        return self.text

    def set_text(self, text: str):
        self.text = text


class SystemFeedback(models.Model):
    class SystemFeedbackType(models.TextChoices):
        Technical = 'T', _('Technical')
        Other = 'O', _('Other')

    class SystemFeedbackStatus(models.TextChoices):
        New = 'N', _('New')
        Viewed = 'V', _('Viewed')
        Replied = 'R', _('Replied')

    text = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=1, choices=SystemFeedbackType.choices, default=SystemFeedbackType.Other)
    status = models.CharField(max_length=1, choices=SystemFeedbackStatus.choices, default=SystemFeedbackStatus.New)
    user = models.ForeignKey(accounts.models.NormalUser, on_delete=models.CASCADE)
    reply = models.ForeignKey(SystemFeedbackReply, on_delete=models.CASCADE, null=True, blank=True)

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


class SystemFeedbackCatalogue(Singleton):
    feedbacks = SystemFeedback.objects.all()

    def get_system_feedback_list(self):
        return self.feedbacks

    def search_by_type(self, type):
        pass

    def search_by_status(self, status):
        pass

    def sort_by_time(self, ascending=True):
        pass