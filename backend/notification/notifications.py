from abc import ABC

from django.db import models

from core.models import Request
from notification.models import Notification
from utils.Singleton import Singleton
from chat.models import Message


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
        NotificationBuilder().create_notification(request.customer.normal_user.user,
                                                  title="اعلام آمادگی کارشناسی برای درخواست شما",
                                                  message=f"متخصص با نام "
                                                          f"{request.specialist.normal_user.user.full_name} "
                                                          f" برای درخواست شما با شرح "
                                                          f"{request.description} "
                                                          f"اعلام آمادگی کرده است.\n",
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"#")


class RequestAcceptanceFinalizeByCustomerNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        NotificationBuilder().create_notification(request.specialist.normal_user.user,
                                                  title="تایید شما توسط مشتری",
                                                  message=f"شما برای انجام درخواست با شرح "
                                                          f"{request.description} "
                                                          f" توسط مشتری با نام "
                                                          f"{request.customer.normal_user.user.full_name} "
                                                          f"تایید شدید. \n",
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"#")


class RequestRejectFinalizeByCustomerNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        NotificationBuilder().create_notification(request.specialist.normal_user.user,
                                                  title="رد شدن شما توسط مشتری",
                                                  message=f"درخواست شما برای انجام خدمت با شرح "
                                                          f"{request.description} "
                                                          f" توسط مشتری با نام "
                                                          f"{request.customer.normal_user.user.full_name} "
                                                          f"رد شد. \n",
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"#")


class RequestAcceptanceFinalizeBySpecialistNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        NotificationBuilder().create_notification(request.customer.normal_user.user,
                                                  title="پذیرش درخواست توسط متخصص",
                                                  message=f"کارشناس با نام "
                                                          f"{request.customer.normal_user.user.full_name} "
                                                          f"درخواست شما با شرح "
                                                          f"{request.description} "
                                                          f"را پذیرفت. \n",
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"#")


class RequestRejectFinalizeBySpecialistNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        NotificationBuilder().create_notification(request.customer.normal_user.user,
                                                  title="رد درخواست توسط متخصص",
                                                  message=f"کارشناس با نام "
                                                          f"{request.customer.normal_user.user.full_name} "
                                                          f"درخواست شما با شرح "
                                                          f"{request.description} "
                                                          f"را رد کرد. \n",
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"#")


class SelectSpecialistForRequestNotification(BaseNotification):
    def __init__(self, request: Request):
        super().__init__(request)

    def build(self):
        request: Request = self.entity
        NotificationBuilder().create_notification(request.specialist.normal_user.user,
                                                  title="انتخاب شما برای انجام درخواست",
                                                  message=f"مشتری با نام "
                                                          f"{request.customer.normal_user.user.full_name} "
                                                          f"از شما برای انجام خدمات با شرح "
                                                          f"{request.description} "
                                                          f"درخواست کرده است. \n",
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"#")


class NewMessageNotification(BaseNotification):
    def __init__(self, message: Message):
        super().__init__(message)

    def build(self):
        message: Message = self.entity
        NotificationBuilder().create_notification(message.receiver.user,
                                                  title="پیام جدید",
                                                  message=f"{message.sender.user.full_name} "
                                                          f"یک پیام جدید برای شما ارسال کرد.\n ",
                                                  type=Notification.NotificationType.INFO,
                                                  link=f"/dashboard/chats/{message.sender.user.id}"
                                                  )
