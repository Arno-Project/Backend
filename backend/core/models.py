from __future__ import annotations

from datetime import datetime

from django.db import models
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _

from accounts.models import Customer, Specialist, Speciality, User, UserCatalogue, SpecialityCatalogue
from core.constants import *
from utils.Singleton import Singleton
from utils.helper_funcs import ListAdapter


class Location(models.Model):
    address = models.TextField(null=False, blank=False)
    latitude = models.DecimalField(null=False, blank=False, max_digits=22,
                                   decimal_places=16)
    longitude = models.DecimalField(null=False, blank=False, max_digits=22,
                                    decimal_places=16)

    def get_address(self):
        return self.address

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude

    def set_latitude(self, latitude):
        self.latitude = latitude

    def set_address(self, address):
        self.address = address

    def set_longitude(self, longitude):
        self.longitude = longitude

    def __str__(self):
        return self.address


class LocationCatalogue(metaclass=Singleton):
    locations = Location.objects.all()

    def search(self, query):
        print("Location Catalogue", query)
        result = self.locations
        for field in ['address']:
            if query.get(field):
                result = result.filter(Q(**{field + '__icontains': query[field]}))
        if query.get('latitude'):
            result = result.filter(latitude__exact=query['latitude'])
        if query.get('longitude'):
            result = result.filter(longitude__exact=query['longitude'])

        return result


class Request(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'PEND', _(PENDING_STRING)
        WAITING_FOR_CUSTOMER_ACCEPTANCE_FROM_SPECIALIST = 'WAIC', _(
            WAITING_FOR_CUSTOMER_ACCEPTANCE_FROM_SPECIALIST_STRING)
        WAITING_FOR_SPECIALIST_ACCEPTANCE_FROM_CUSTOMER = 'WAIS', _(
            WAITING_FOR_SPECIALIST_ACCEPTANCE_FROM_CUSTOMER_STRING)
        IN_PROGRESS = 'PROG', _(IN_PROGRESS_STRING)
        DONE = 'DONE', _(DONE_STRING)
        CANCELED = 'CNCL', _(CANCELED_STRING)
        REJECTED = 'REJC', _(REJECTED_STRING)

    customer = models.ForeignKey(Customer, null=False, blank=False, on_delete=models.DO_NOTHING)
    specialist = models.ForeignKey(Specialist, null=True, blank=True, on_delete=models.DO_NOTHING)
    requested_speciality = models.ForeignKey(Speciality, null=False, blank=False, on_delete=models.DO_NOTHING)
    desired_start_time = models.DateTimeField(null=False, blank=False)

    description = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=4, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.DO_NOTHING)

    def get_customer(self):
        return self.customer

    def get_specialist(self):
        return self.specialist

    def get_requested_speciality(self):
        return self.requested_speciality

    def get_desired_start_time(self):
        return self.desired_start_time

    def get_description(self):
        return self.description

    def get_status(self):
        return self.status

    def get_created_at(self):
        return self.created_at

    def get_updated_at(self):
        return self.updated_at

    def get_accepted_at(self):
        return self.accepted_at

    def get_completed_at(self):
        return self.completed_at

    def get_location(self):
        return self.location

    def set_customer(self, customer: "Customer"):
        self.customer = customer

    def set_specialist(self, specialist: "Specialist"):
        self.specialist = specialist

    def set_requested_speciality(self, requested_speciality: "Speciality"):
        self.requested_speciality = requested_speciality

    def set_desired_start_time(self, desired_start_time: datetime):
        self.desired_start_time = desired_start_time

    def set_description(self, description: str):
        self.description = description

    def set_status(self, status: str):
        self.status = status

    def set_created_at(self, created_at: datetime):
        self.created_at = created_at

    def set_updated_at(self, updated_at: datetime):
        self.updated_at = updated_at

    def set_accepted_at(self, accepted_at: datetime):
        self.accepted_at = accepted_at

    def set_completed_at(self, completed_at: datetime):
        self.completed_at = completed_at

    def set_location(self, location: "Location"):
        self.location = location

    def remove_specialist(self):
        self.specialist = None
        self.save()

    def cancel(self):
        self.set_status(Request.RequestStatus.CANCELED)
        self.save()
    
    def mark_as_finished(self):
        self.set_status(Request.RequestStatus.DONE)
        self.set_completed_at(datetime.now())
        self.save()

class RequestCatalogue(metaclass=Singleton):
    requests = Request.objects.all()

    def search(self, query: dict):
        result = self.requests

        if query.get('id'):
            result = result.filter(pk__in=ListAdapter().python_ensure_list(query['id']))

        if query.get('customer'):
            customer_query = {
                **query.get('customer'),
                'role': User.UserRole.Customer
            }
            users = UserCatalogue().search(query=customer_query)
            result = result.filter(customer__normal_user__user__in=users)

        if query.get('specialist'):
            specialist_query = {
                **query.get('specialist'),
                'role': User.UserRole.Specialist
            }
            users = UserCatalogue().search(query=specialist_query)
            result = result.filter(specialist__normal_user__user__in=users)

        if query.get('speciality'):
            speciality_query = query.get('speciality')['id']
            result = result.filter(requested_speciality__in=speciality_query)

        if query.get('location'):
            locations = LocationCatalogue().search(query=query.get('location'))
            result = result.filter(location__in=locations)

        if query.get('status'):
            result = result.filter(status__iexact=query.get('status'))

        for field in ['description']:
            if query.get(field):
                result = result.filter(**{field + "__icontains": query.get(field)})

        for field in ['desired_start_time_gte', 'accepted_at_gte', 'completed_at_gte']:
            if query.get(field):
                result = result.filter(**{'_'.join(field.split('_')[:-1]) + "__gte": query.get(field)})

        for field in ['desired_start_time_lte', 'accepted_at_lte', 'completed_at_lte']:
            if query.get(field):
                result = result.filter(**{'_'.join(field.split('_')[:-1]) + "__lte": query.get(field)})

        return result

    def get_requests(self):
        return self.requests

    def sort_by_time(self):
        return self.requests.order_by('desired_start_time')

    def sort_by_popularity(self, queryset):
        return queryset.values('requested_speciality').annotate(
            count=Count('requested_speciality')).order_by("-count")

    def sort_by_popularity_category(self, queryset):
        return queryset.values('requested_speciality__parent').annotate(
            count=Count('requested_speciality__parent')).order_by("-count")
