from django.contrib import admin

# Register your models here.
from feedback import models

admin.site.register(models.Feedback)
admin.site.register(models.SystemFeedback)
admin.site.register(models.EvaluationMetric)
admin.site.register(models.MetricScore)