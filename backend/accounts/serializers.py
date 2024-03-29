from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from accounts.models import User, Customer, Specialist, TechnicalManager, CompanyManager, Speciality, NormalUser, \
    ManagerUser


class FlattenMixin(object):
    """Flatens the specified related objects in this representation"""

    def to_representation(self, obj):
        assert hasattr(self.Meta, 'flatten'), (
            'Class {serializer_class} missing "Meta.flatten" attribute'.format(
                serializer_class=self.__class__.__name__
            )
        )
        # Get the current object representation
        rep = super(FlattenMixin, self).to_representation(obj)
        # Iterate the specified related objects with their serializer
        for field, serializer_class in self.Meta.flatten:
            serializer = serializer_class(context=self.context)
            objrep = serializer.to_representation(getattr(obj, field))
            for key in objrep:
                rep[key] = objrep[key]
        return rep


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'role', 'last_login', 'date_joined')


class UserFullSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'first_name', 'last_name', 'date_joined', 'last_login', 'role')


class NormalUserSerializer(ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = NormalUser
        fields = ('score', 'user')


class NormalUserFullSerializer(ModelSerializer):
    user = UserFullSerializer()

    class Meta:
        model = NormalUser
        fields = ('score', 'user')


class ManagerUserSerializer(ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = ManagerUser
        fields = ('user',)


class ManagerUserFullSerializer(ModelSerializer):
    user = UserFullSerializer()

    class Meta:
        model = ManagerUser
        fields = ('user',)


class CustomerSerializer(FlattenMixin, ModelSerializer):
    class Meta:
        model = Customer
        fields = ('id',)
        flatten = [('normal_user', NormalUserSerializer)]


class CustomerFullSerializer(FlattenMixin, ModelSerializer):
    class Meta:
        model = Customer
        fields = ('id',)
        flatten = [('normal_user', NormalUserFullSerializer)]




class SpecialityBasicSerializer(ModelSerializer):
    class Meta:
        model = Speciality
        fields = ('id', 'title', 'description')


class SpecialitySerializer(ModelSerializer):
    parent = SpecialityBasicSerializer()

    def get_fields(self):
        fields = super(SpecialitySerializer, self).get_fields()
        fields['children'] = SpecialitySerializer(many=True)
        return fields

    class Meta:
        model = Speciality
        fields = ('id', 'title', 'description', 'parent', 'children')


class SpecialityCreationSerializer(ModelSerializer):
    class Meta:
        model = Speciality
        fields = ('id', 'title', 'description', 'parent')


class SpecialistSerializer(FlattenMixin, ModelSerializer):
    speciality = SpecialitySerializer(read_only=True, many=True)

    class Meta:
        model = Specialist
        fields = ('id', 'speciality', 'is_validated')
        flatten = [('normal_user', NormalUserSerializer)]


class SpecialistFullSerializer(SpecialistSerializer):
    class Meta(SpecialistSerializer.Meta):
        flatten = [('normal_user', NormalUserFullSerializer)]


class CompanyManagerSerializer(FlattenMixin, ModelSerializer):
    class Meta:
        model = CompanyManager
        fields = ('id',)
        flatten = [('manager_user', ManagerUserSerializer)]


class CompanyManagerFullSerializer(FlattenMixin, ModelSerializer):
    class Meta:
        model = CompanyManager
        fields = ('id',)
        flatten = [('manager_user', ManagerUserFullSerializer)]


class TechnicalManagerFullSerializer(FlattenMixin, ModelSerializer):
    class Meta:
        model = CompanyManager
        fields = ('id',)
        flatten = [('manager_user', ManagerUserFullSerializer)]


class TechnicalManagerSerializer(FlattenMixin, ModelSerializer):
    class Meta:
        model = TechnicalManager
        fields = ('id',)
        flatten = [('manager_user', ManagerUserSerializer)]


class RegisterSerializerFactory:
    def __init__(self, concrete_class, middle_class):
        self.concrete_class = concrete_class
        self.middle_class = middle_class

    def get_serializer(self):
        concrete_class = self.concrete_class
        middle_class = self.middle_class
        role_mapping = {
            Customer: User.UserRole.Customer,
            Specialist: User.UserRole.Specialist,
            CompanyManager: User.UserRole.CompanyManager,
            TechnicalManager: User.UserRole.TechnicalManager
        }

        class Serializer(ModelSerializer):
            class Meta:
                model = User
                fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'phone')
                extra_kwargs = {'password': {'write_only': True}}

            def create(self, validated_data):
                user = User.objects.create_user(
                    validated_data['username'], validated_data['email'], validated_data['password'],
                    phone=validated_data['phone'],
                    first_name=validated_data['first_name'], last_name=validated_data['last_name'],
                    role=role_mapping[concrete_class])
                user.save()
                middle_user = middle_class.objects.create(user=user)
                middle_user.save()
                if concrete_class == Customer or concrete_class == Specialist:
                    concrete_user = concrete_class.objects.create(normal_user=middle_user)
                elif concrete_class == CompanyManager or concrete_class == TechnicalManager:
                    concrete_user = concrete_class.objects.create(manager_user=middle_user)
                else:
                    raise Exception("Unknown user type")
                concrete_user.save()
                return concrete_user

        return Serializer
