from abc import ABC

from chat.models import Message
from core.models import Request
from notification.constants import *
from notification.models import Notification
from utils.Singleton import Singleton


class NotificationBuilder(metaclass=Singleton):
    def create_notification(self, user, title="", message="", type=Notification.NotificationType.INFO, link=""):
        notif = Notification()
        notif.set_user(user)
        notif.set_title(title)
        notif.set_message(message)
        notif.set_type(type)
        notif.set_is_read(False)
        notif.set_link(link)
        notif.save()


class BaseNotification(ABC):
    entity = None

    def __init__(self, entity):
        self.entity = entity

    def build(self):
        pass


class RequestInitialAcceptBySpecialistNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        message = RequestInitialAcceptBySpecialistNotification_message.format(
            request.specialist.normal_user.user.full_name, request.description
        )
        NotificationBuilder().create_notification(request.customer.normal_user.user,
                                                  title=RequestInitialAcceptBySpecialistNotification_title,
                                                  message=message,
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"/dashboard/request_details/{request.id}")


class RequestAcceptanceFinalizeByCustomerNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        message = RequestAcceptanceFinalizeByCustomerNotification_message.format(request.description,
                                                                                 request.customer.normal_user.user.full_name)
        NotificationBuilder().create_notification(request.specialist.normal_user.user,
                                                  title=RequestAcceptanceFinalizeByCustomerNotification_title,
                                                  message=message,
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"/dashboard/request_details/{request.id}")


class RequestRejectFinalizeByCustomerNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        message = RequestRejectFinalizeByCustomerNotification_message.format(request.description,
                                                                             request.customer.normal_user.user.full_name)
        NotificationBuilder().create_notification(request.specialist.normal_user.user,
                                                  title=RequestRejectFinalizeByCustomerNotification_title,
                                                  message=message,
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"/dashboard/request_details/{request.id}")


class RequestAcceptanceFinalizeBySpecialistNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        message = RequestAcceptanceFinalizeBySpecialistNotification_message.format(
            request.specialist.normal_user.user.full_name, request.description)
        NotificationBuilder().create_notification(request.customer.normal_user.user,
                                                  title=RequestAcceptanceFinalizeBySpecialistNotification_title,
                                                  message=message,
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"/dashboard/request_details/{request.id}")


class RequestRejectFinalizeBySpecialistNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        message = RequestRejectFinalizeBySpecialistNotification_message.format(
            request.specialist.normal_user.user.full_name, request.description)
        NotificationBuilder().create_notification(request.customer.normal_user.user,
                                                  title=RequestRejectFinalizeBySpecialistNotification_title,
                                                  message=message,
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"/dashboard/request_details/{request.id}")


class SelectSpecialistForRequestNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        message = SelectSpecialistForRequestNotification_message.format(request.customer.normal_user.user.full_name,
                                                                        request.description)
        NotificationBuilder().create_notification(request.specialist.normal_user.user,
                                                  title=SelectSpecialistForRequestNotification_title,
                                                  message=message,
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"/dashboard/request_details/{request.id}")


class NewMessageNotification(BaseNotification):
    def __init__(self, message: Message):
        super().__init__(message)

    def build(self):
        message: Message = self.entity
        notification_message = NewMessageNotification_message.format(message.sender.user.full_name)
        NotificationBuilder().create_notification(message.receiver.user,
                                                  title=NewMessageNotification_title,
                                                  message=notification_message,
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"/dashboard/chats/{message.sender.user.id}"
                                                  )
