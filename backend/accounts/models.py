from typing import List

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from phone_field import PhoneField

from accounts.constants import *
from utils.Singleton import Singleton
from utils.helper_funcs import ListAdapter


class User(AbstractUser):
    class UserRole(models.TextChoices):
        CompanyManager = 'CM', _('Company Manager')
        TechnicalManager = 'TM', _('Technical Manager')
        Customer = 'C', _('Customer')
        Specialist = 'S', _('Specialist')

    email = models.EmailField(unique=True)
    phone = PhoneField(blank=False, null=False, verbose_name=PHONE_NUMBER_VERBOSE, unique=True)
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
        verbose_name = USER_VERBOSE_NAME
        verbose_name_plural = USER_VERBOSE_NAME_PLURAL

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

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
        verbose_name = NORMAL_USER_VERBOSE_NAME
        verbose_name_plural = NORMAL_USER_VERBOSE_NAME_PLURAL


class Customer(models.Model):
    normal_user = models.OneToOneField(NormalUser, on_delete=models.CASCADE, related_name='customer_normal_user')

    def __str__(self):
        return self.normal_user.__str__()

    class Meta:
        verbose_name = CUSTOMER_VERBOSE_NAME
        verbose_name_plural = CUSTOMER_VERBOSE_NAME_PLURAL


class Speciality(models.Model):
    title = models.CharField(max_length=100, verbose_name=SPECIALITY_TITLE)
    description = models.TextField(verbose_name=SPECIALITY_DESCRIPTION)

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
            result = result.filter(pk__in=ListAdapter().python_ensure_list(query.get('id')))
        for field in ['title', 'description']:
            if query.get(field):
                result = result.filter(Q(**{field + '__icontains': query[field]}))
        return result


class Specialist(models.Model):
    class Meta:
        verbose_name = SPECIALIST_VERBOSE_NAME
        verbose_name_plural = SPECIALIST_VERBOSE_NAME_PLURAL

    normal_user = models.OneToOneField(NormalUser, on_delete=models.CASCADE, related_name='specialist_normal_user')
    speciality = models.ManyToManyField(Speciality, blank=True, null=True)
    documents = models.FileField(upload_to='documents/', blank=True, null=True)
    is_validated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.normal_user.__str__()

    def add_speciality(self, speciality: "Speciality"):
        self.speciality.add(speciality)

    def remove_speciality(self, speciality: "Speciality"):
        self.speciality.remove(speciality)

    def get_speciality(self):
        return self.speciality.all()

    def upload_document(self, document):
        pass

    def remove_document(self):
        pass

    def get_is_validated(self):
        return self.is_validated

    def set_validated(self, is_validated: bool):
        self.is_validated = is_validated

    def get_is_active(self):
        return self.is_active

    def set_active(self, is_active: bool):
        self.is_active = is_active

class ManagerUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="manager_user_user")

    def confirm_specialist(self, specialist: Specialist):
        specialist.set_validated(True)
        specialist.save()

    def __str__(self):
        return self.user.__str__()

    class Meta:
        verbose_name = MANAGER_USER_VERBOSE_NAME
        verbose_name_plural = MANAGER_USER_VERBOSE_NAME_PLURAL


class CompanyManager(models.Model):
    manager_user = models.OneToOneField(ManagerUser, on_delete=models.CASCADE,
                                        related_name='company_manager_manager_user')

    def __str__(self):
        return self.manager_user.__str__()

    def add_new_manager(self, username: str, password: str, email: str, phone: str):
        pass

    class Meta:
        verbose_name = COMPANY_MANAGER_VERBOSE_NAME
        verbose_name_plural = COMPANY_MANAGER_VERBOSE_NAME_PLURAL


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
                result = result.filter(pk__in=ListAdapter().python_ensure_list(query[field]))
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


