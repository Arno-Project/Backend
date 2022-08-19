from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from utils.Singleton import Singleton


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        INFO = 'INF', _("Information")
        ERROR = 'ERR', _("Error")
        SUCCESS = 'SUC', _("Success")

    title = models.CharField(max_length=100, null=False, blank=True, default='')
    message = models.TextField(null=True, blank=True, default=None)
    link = models.CharField(null=True, blank=True, default=None, max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(null=False, blank=False, default=False)
    user = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=3, choices=NotificationType.choices, default=NotificationType.INFO)

    def __str__(self):
        return f"{self.title} - {self.message}"

    def get_title(self):
        return self.title

    def get_message(self):
        return self.message

    def get_is_read(self):
        return self.is_read

    def get_user(self):
        return self.user

    def get_type(self):
        return self.notification_type

    def get_link(self):
        return self.link

    def get_date(self):
        return self.date

    def set_title(self, title):
        self.title = title

    def set_message(self, message):
        self.message = message

    def set_is_read(self, is_read):
        self.is_read = is_read

    def set_user(self, user):
        self.user = user

    def set_type(self, type):
        self.notification_type = type

    def set_link(self, link):
        self.link = link


class NotificationCatalogue(metaclass=Singleton):
    @property
    def notifications(self):
        return Notification.objects.all()

    def get_by_id(self, id):
        return self.notifications.get(pk=id)

    def get_unread(self, user):
        return self.notifications.filter(user=user, is_read=False).order_by('-date')

    def get_read(self, user):
        return self.notifications.filter(user=user, is_read=True).order_by('-date')

    def get_all(self, user):
        return self.notifications.filter(user=user).order_by('-date')
