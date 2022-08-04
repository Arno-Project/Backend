from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, QuerySet, When, Case

from accounts.models import NormalUser
from utils.Singleton import Singleton
import accounts.models


class Message(models.Model):
    class MessageType(models.TextChoices):
        System = 'S', _('System')
        User = 'U', _('User')

    created_at = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(
        accounts.models.NormalUser, on_delete=models.CASCADE, related_name='send_messages')
    receiver = models.ForeignKey(
        accounts.models.NormalUser, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField(null=False, blank=False)
    type = models.CharField(max_length=1, choices=MessageType.choices)
    is_read = models.BooleanField(default=False)

    def get_time(self):
        return self.created_at

    def get_sender(self):
        return self.sender

    def get_receiver(self):
        return self.receiver

    def get_text(self):
        return self.text


class MessageCatalogue(metaclass=Singleton):
    messages = Message.objects.all()

    def search(self, user: NormalUser, peer_id:int = None):
        if not peer_id: 
            return self.messages\
                .filter(Q(sender__user__pk=user.pk) | Q(receiver__user__pk=user.pk))\
                .annotate(peer=Case(
                    When(sender__user__pk=user.pk, then='receiver'),
                    When(receiver__user__pk=user.pk, then='sender'),
                ))\
                .order_by('peer', '-created_at')\
                .distinct('peer')
        else:
            return self.messages\
                .filter(
                    (Q(sender__user__pk=user.pk) & Q(receiver__user__pk=peer_id)) |
                    (Q(sender__user__pk=peer_id) & Q(receiver__user__pk=user.pk))
                )\
                .order_by('-created_at')
