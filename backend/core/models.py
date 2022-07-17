# Create your models here.
from django.utils.translation import gettext_lazy as _

from accounts.models import *


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


class Request(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'PEND', _('pending')
        WAIT = 'WAIT', _('Waiting for acceptance of the specialist from customer')
        IN_PROGRESS = 'PROG', _('In Progress')
        DONE = 'DONE', _('done')
        CANCELED = 'CNCL', _('Canceled')
        REJECTED = 'REJC', _('Rejected')

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

    @classmethod
    def search(cls, query: dict):
        result = cls.objects

        if query.get('customer'):
            print(query.get('customer'))
            users = Customer.search(query.get('customer'))
            result = cls.objects.filter(customer__in=users)
        if query.get('specialist'):
            users = Specialist.search(query.get('specialist'))
            result = cls.objects.filter(specialist__in=users)
        if query.get('speciality'):
            specialities = Speciality.search(query.get('speciality'))
            result = cls.objects.filter(requested_speciality__in=specialities)
        for field in ['address', 'description']:
            if query.get(field):
                result = result.filter(**{field + "__icontains": query.get(field)})
        if query.get('date_from'):
            result = result.filter(requested_date__gte=query.get('date_from'))
        if query.get('date_to'):
            result = result.filter(requested_date__lte=query.get('date_to'))

        return result


class RequestCatalogue(Singleton):
    requests = Request.objects.all()

    def get_requests(self):
        return self.requests

    def search_by_speciality(self, speciality: "Speciality"):
        return self.requests.filter(requested_speciality=speciality)

    def search_by_customer(self, customer: "Customer"):
        return self.requests.filter(customer=customer)

    def search_by_specialist(self, specialist: "Specialist"):
        return self.requests.filter(specialist=specialist)

    def search_by_status(self, status: str):
        return self.requests.filter(status=status)

    def sort_by_time(self):
        return self.requests.order_by('desired_start_time')
