import datetime
from typing import List

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from phone_field import PhoneField

from core.models import Request
from utils.Singleton import Singleton


class User(AbstractUser):
    phone = PhoneField(blank=False, null=False, verbose_name=u"شماره تلفن همراه", unique=True)

    class Meta:
        abstract = True
        verbose_name = u"کاربر"
        verbose_name_plural = u"کاربران"

    def get_role(self):
        role = 'customer'
        try:
            _ = self.specialist
            role = 'specialist'
        except ObjectDoesNotExist:
            pass
        try:
            _ = self.companymanager
            role = 'companyManager'
        except ObjectDoesNotExist:
            pass
        try:
            _ = self.technicalmanager
            role = 'technicalManager'
        except ObjectDoesNotExist:
            pass

        return role

    @classmethod
    def search(cls, query: dict, is_customer=False, is_specialist=False, is_company_manager=False,
               is_technical_manager=False):
        result = cls.objects
        if is_customer:
            result.filter(customer__isnull=False)
        elif is_specialist:
            result.filter(specialist__isnull=False)
        elif is_company_manager:
            result.filter(company_manager__isnull=False)
        elif is_technical_manager:
            result.filter(technical_manager__isnull=False)

        for field in ['first_name', 'last_name', 'phone']:
            if query.get(field):
                result = result.filter(Q(**{field + '__icontains': query[field]}))
        if query.get('username'):
            result = result.filter(Q(username__eq=query['username']))
        # filter User objects that exist in Customer Table

        return result

    def get_email(self):
        return self.email

    def get_phone(self):
        return self.phone

    def get_username(self):
        return self.username

    def get_is_active(self):
        return self.is_active

    def set_phone(self, phone):
        self.phone = phone

    def set_active(self, is_active):
        self.is_active = is_active


class NormalUser(User):
    score = models.IntegerField(default=0)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def get_score(self):
        return self.score

    def set_score(self, score):
        self.score = score

    def send_message(self, message, receiver: "NormalUser"):
        pass

    def receive_messages(self, sender: "NormalUser") -> List["Message"]:
        pass

    class Meta:
        abstract = True
        verbose_name = u"کاربر"
        verbose_name_plural = u"کاربران"


class Customer(models.Model):
    class Meta:
        verbose_name = u"مشتری"
        verbose_name_plural = u"مشتریان"

    def submit_request(self, requested_speciality: "Speciality", requested_date: datetime.datetime, description: str,
                       address: str):
        pass

    def delete_request(self, request: "Request"):
        pass

    def edit_request(self, request: "Request", requested_speciality: "Speciality", requested_date: datetime.datetime,
                     description: str, address: str):
        pass

    def select_specialist(self, specialist: "Specialist"):
        pass

    def accept_specialist(self, request: "Request"):
        pass

    def reject_specialist(self, request: "Request"):
        pass

    def submit_feedback(self, request: "Request", feedback: str, score: int):
        pass

    @classmethod
    def search(cls, query):
        result = User.search(query, is_customer=True)
        result = cls.objects.filter(user__in=result)
        return result


class Speciality(models.Model):
    title = models.CharField(max_length=100, verbose_name=u"نام تخصص")
    description = models.TextField(verbose_name=u"توضیحات")

    def get_title(self):
        return self.title

    def set_title(self, title):
        self.title = title

    def get_description(self):
        return self.description

    def set_description(self, description):
        self.description = description

    @classmethod
    def search(cls, query):
        result = cls.objects
        for field in ['name']:
            if query.get(field):
                result = result.filter(Q(**{field + '__icontains': query[field]}))


class Specialist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    speciality = models.ManyToManyField(Speciality, blank=True, null=True)
    documents = models.FileField(upload_to='documents/', blank=True, null=True)

    def add_speciality(self, speciality: "Speciality"):
        pass

    def remove_speciality(self, speciality: "Speciality"):
        pass

    def upload_document(self, document):
        pass

    def remove_document(self):
        pass

    def accept_request(self, request: "Request"):
        pass

    def reject_request(self, request: "Request"):
        pass

    def submit_feedback(self, request: "Request", feedback: str, score: int):
        pass

    def submit_request_fullfillment(self, request: "Request"):
        pass

    @classmethod
    def search(cls, query):
        result = User.search(query, is_specialist=True)
        result = cls.objects.filter(user__in=result)
        for field in ['speciality']:
            if query.get(field):
                result = result.filter(Q(**{'specialist__' + field + '__icontains': query[field]}))
        return result


class CompanyManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def add_new_manager(self, username: str, password: str, email: str, phone: str):
        pass

    @classmethod
    def search(cls, query):
        result = User.search(query, is_company_manager=True)
        result = cls.objects.filter(user__in=result)
        return result


class TechnicalManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    @classmethod
    def search(cls, query):
        result = User.search(query, is_technical_manager=True)
        result = cls.objects.filter(user__in=result)
        return result


# create singleton class for UserCatalogue

class UserCatalogue(metaclass=Singleton):
    users = User.objects.all()

    def search_by_username(self, username):
        return self.users.filter(username=username)

    def search_by_phone(self, phone):
        return self.users.filter(phone=phone)

    def search_by_role(self, role):
        pass

    def search_by_name(self, name):
        pass

    def search_by_speciality(self, speciality):
        pass

    def search_by_date(self, date):
        pass

    def search_by_active(self, active):
        pass

    def sort_by_join_date(self, ascending):
        pass
