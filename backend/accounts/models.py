import datetime
from typing import List

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _
from phone_field import PhoneField

from utils.Singleton import Singleton


class User(AbstractUser):
    class UserRole(models.TextChoices):
        CompanyManager = 'CM', _('Company Manager')
        TechnicalManager = 'TM', _('Technical Manager')
        Customer = 'C', _('Customer')
        Specialist = 'S', _('Specialist')

    email = models.EmailField(unique=True)
    phone = PhoneField(blank=False, null=False, verbose_name=u"شماره تلفن همراه", unique=True)
    role = models.CharField(max_length=2, choices=UserRole.choices, default=UserRole.Customer)

    @property
    def is_manager(self):
        return self.role in [self.UserRole.CompanyManager, self.UserRole.TechnicalManager]

    @property
    def full_user(self):
        if self.role == User.UserRole.Customer:
            return self.normal_user_user.customer_normal_user
        elif self.role == User.UserRole.Specialist:
            return self.normal_user_user.specialist_normal_user
        elif self.role == User.UserRole.CompanyManager:
            return self.manager_user_user.company_manager_manager_user
        elif self.role == User.UserRole.TechnicalManager:
            return self.manager_user_user.technical_manager_manger_user

    @property
    def general_user(self):
        if self.role == User.UserRole.Customer or self.role == User.UserRole.Specialist:
            return self.normal_user_user
        elif self.role == User.UserRole.CompanyManager or self.role == User.UserRole.TechnicalManager:
            return self.manager_user_user

    class Meta:
        verbose_name = u"کاربر"
        verbose_name_plural = u"کاربران"

    def get_role(self):
        return self.role

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


class NormalUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="normal_user_user")
    score = models.IntegerField(default=0)

    def __str__(self):
        return self.user.__str__()

    def get_score(self):
        return self.score

    def set_score(self, score):
        self.score = score

    def send_message(self, message, receiver: "NormalUser"):
        pass

    def receive_messages(self, sender: "NormalUser") -> List["Message"]:
        pass

    class Meta:
        verbose_name = u"کاربر عادی"
        verbose_name_plural = u" کاربران عادی"


class Customer(models.Model):
    normal_user = models.OneToOneField(NormalUser, on_delete=models.CASCADE, related_name='customer_normal_user')

    def __str__(self):
        return self.normal_user.__str__()

    class Meta:
        verbose_name = u"مشتری"
        verbose_name_plural = u"مشتریان"

    def submit_request(self, requested_speciality: "Speciality", requested_date: datetime.datetime, description: str,
                       address: str):
        pass

    def delete_request(self, request):
        pass

    def edit_request(self, request, requested_speciality: "Speciality", requested_date: datetime.datetime,
                     description: str, address: str):
        pass

    def select_specialist(self, specialist: "Specialist"):
        pass

    def accept_specialist(self, request):
        pass

    def reject_specialist(self, request):
        pass

    def submit_feedback(self, request, feedback: str, score: int):
        pass


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


class SpecialityCatalogue(metaclass=Singleton):
    specialities = Speciality.objects.all()

    def search(self, query):
        result = self.specialities
        if query.get('id'):
            result = result.filter(pk__in=query.get('id'))
        for field in ['name', 'description']:
            if query.get(field):
                result = result.filter(Q(**{field + '__icontains': query[field]}))
        return result


class Specialist(models.Model):
    class Meta:
        verbose_name = u"متخصص"
        verbose_name_plural = u"متخصصان"

    normal_user = models.OneToOneField(NormalUser, on_delete=models.CASCADE, related_name='specialist_normal_user')
    speciality = models.ManyToManyField(Speciality, blank=True, null=True)
    documents = models.FileField(upload_to='documents/', blank=True, null=True)
    is_validated = models.BooleanField(default=False)

    def __str__(self):
        return self.normal_user.__str__()

    def add_speciality(self, speciality: "Speciality"):
        self.speciality.add(speciality)

    def remove_speciality(self, speciality: "Speciality"):
        self.speciality.remove(speciality)

    def get_speciality(self):
        return self.speciality

    def upload_document(self, document):
        pass

    def remove_document(self):
        pass

    def accept_request(self, request):
        pass

    def reject_request(self, request):
        pass

    def submit_feedback(self, request, feedback: str, score: int):
        pass

    def submit_request_fullfillment(self, request):
        pass


class ManagerUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="manager_user_user")

    def confirm_specialist(self, specialist: Specialist):
        specialist.is_validated = True
        specialist.save()

    def __str__(self):
        return self.user.__str__()


class CompanyManager(models.Model):
    manager_user = models.OneToOneField(ManagerUser, on_delete=models.CASCADE,
                                        related_name='company_manager_manager_user')

    def __str__(self):
        return self.manager_user.__str__()

    def add_new_manager(self, username: str, password: str, email: str, phone: str):
        pass


class TechnicalManager(models.Model):
    manager_user = models.OneToOneField(ManagerUser, on_delete=models.CASCADE,
                                        related_name='technical_manager_manger_user')

    def __str__(self):
        return self.manager_user.__str__()


class UserCatalogue(metaclass=Singleton):
    users = User.objects.all()

    def search(self, query):
        result = self.users
        print(query)

        if not query:
            return result
        for field in ['id']:
            if query.get(field):
                result = result.filter(pk__in=query[field])
        for field in ['first_name', 'last_name', 'phone']:
            if query.get(field):
                result = result.filter(Q(**{field + '__icontains': query[field]}))
        if query.get('username'):
            result = result.filter(Q(username__eq=query['username']))
        # filter User objects that exist in Customer Table
        if query.get('role'):
            result = result.filter(Q(role__icontains=query['role']))
            if query['role'] == User.UserRole.Specialist:
                for field in ['speciality']:
                    if query.get(field):
                        result = result.filter(Q(**{'specialist__' + field + '__icontains': query[field]}))
        if query.get('specialist_id'):
            result = result.filter(Q(normal_user_user__specialist_normal_user__exact=query['specialist_id']))
            print(result)

        return result

    def sort_by_join_date(self, ascending):
        pass
