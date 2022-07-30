from django.db import models
from django.utils.translation import gettext_lazy as _

import accounts.models


class Message(models.Model):
    class MessageType(models.TextChoices):
        System = 'S', _('System')
        User = 'U', _('User')

    created_at = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(accounts.models.NormalUser, on_delete=models.CASCADE)
    receiver = models.ForeignKey(accounts.models.NormalUser, on_delete=models.CASCADE)
    text = models.TextField(null=False, blank=False)
    type = models.CharField(max_length=1, choices=MessageType.choices)

    def get_time(self):
        return self.created_at

    def get_sender(self):
        return self.sender

    def get_receiver(self):
        return self.receiver

    def get_text(self):
        return self.text
    