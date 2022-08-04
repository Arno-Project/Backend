from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
# Create your views here.
from knox.auth import TokenAuthentication
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from notification.models import NotificationCatalogue, Notification
from notification.serializers import NotificationSerializer
from utils.helper_funcs import ListAdapter


class NotificationView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request, notification_id=''):
        many = False
        if notification_id:
            notification = NotificationCatalogue().get_by_id(notification_id)
            if notification.get_user() != request.user:
                return Response({
                    'error': _('Notification not found')
                }, status=HTTP_404_NOT_FOUND)
        else:
            notification = NotificationCatalogue().get_unread(request.user)
            many = True

        serializer = NotificationSerializer(notification, many=many)

        return JsonResponse({"notifications": serializer.data})

    def post(self, request):
        ids = request.data.get("ids")
        id_list = ListAdapter().python_ensure_list(ids)
        objs = []
        for id in id_list:
            try:
                notif = Notification.objects.get(pk=id)
            except:
                continue
            if not notif:
                continue
            if notif.get_user() != request.user:
                continue
            notif.set_is_read(True)
            objs.append(notif)
        Notification.objects.bulk_update(objs, ['is_read'])
        return Response({'ids': map(lambda x: x.id, objs)})
