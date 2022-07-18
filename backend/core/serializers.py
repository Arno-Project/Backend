from rest_framework.serializers import ModelSerializer

from accounts.serializers import SpecialistSerializer, CustomerSerializer, SpecialitySerializer
from core.models import Request, Location


class LocationSerializer(ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class RequestSerializer(ModelSerializer):
    specialist = SpecialistSerializer()
    customer = CustomerSerializer()
    requested_speciality = SpecialitySerializer()
    location = LocationSerializer()

    class Meta:
        model = Request
        fields = (
        'id', 'specialist', 'customer', 'location', 'description', 'desired_start_time', 'requested_speciality',
        'status')


class RequestSubmitSerializer(ModelSerializer):
    class Meta:
        model = Request
        fields = ('id', 'customer', 'location', 'description', 'desired_start_time', 'requested_speciality')
