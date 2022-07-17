from rest_framework.serializers import ModelSerializer

from accounts.serializers import SpecialistSerializer, CustomerSerializer, SpecialitySerializer
from core.models import Request, Location


class RequestSerializer(ModelSerializer):
    specialist = SpecialistSerializer()
    customer = CustomerSerializer()
    requested_speciality = SpecialitySerializer()

    class Meta:
        model = Request
        fields = ('id', 'specialist', 'customer', 'description', 'requested_date', 'requested_speciality')


class LocationSerializer(ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'
