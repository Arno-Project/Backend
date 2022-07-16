from rest_framework.serializers import ModelSerializer

from accounts.models import User, Customer, Specialist, TechnicalManager, CompanyManager, Speciality, NormalUser, \
    ManagerUser


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'role')


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
        fields = ('user')


class ManagerUserFullSerializer(ModelSerializer):
    user = UserFullSerializer()

    class Meta:
        model = ManagerUser
        fields = ('user')


class CustomerSerializer(ModelSerializer):
    normal_user = NormalUserSerializer()

    class Meta:
        model = Customer
        fields = ('id', 'normal_user')


class SpecialitySerializer(ModelSerializer):
    class Meta:
        model = Speciality
        fields = ('id', 'name')


class CustomerFullSerializer(ModelSerializer):
    normal_user = NormalUserFullSerializer()

    class Meta:
        model = Customer
        fields = ('id', 'normal_user')


class SpecialistSerializer(ModelSerializer):
    normal_user = NormalUserSerializer()
    speciality = SpecialitySerializer(read_only=True, many=True)

    class Meta:
        model = Specialist
        fields = ('id', 'user', 'speciality')


class SpecialistFullSerializer(ModelSerializer):
    normal_user = NormalUserFullSerializer()

    class Meta:
        model = Specialist
        fields = ('id', 'normal_user')


class CompanyManagerSerializer(ModelSerializer):
    manager_user = ManagerUserSerializer()

    class Meta:
        model = CompanyManager
        fields = ('id', 'manager_user')


class CompanyManagerFullSerializer(ModelSerializer):
    manager_user = ManagerUserFullSerializer()

    class Meta:
        model = CompanyManager
        fields = ('id', 'manager_user')


class TechnicalManagerFullSerializer(ModelSerializer):
    manager_user = ManagerUserFullSerializer()

    class Meta:
        model = CompanyManager
        fields = ('id', 'manager_user')


class TechnicalManagerSerializer(ModelSerializer):
    manager_user = ManagerUserSerializer()

    class Meta:
        model = TechnicalManager
        fields = ('id', 'manager_user')


class RegisterSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'phone')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data['username'], validated_data['email'], validated_data['password'],
            phone=validated_data['phone'],
            first_name=validated_data['first_name'], last_name=validated_data['last_name'],
            role=validated_data['role'])
        user.save()
        return user


class NormalUserRegisterSerializer(RegisterSerializer):
    class Meta(RegisterSerializer.Meta):
        pass

    def create(self, validated_data):
        user = super().create(validated_data)
        normal_user = NormalUser.objects.create(user=user)
        return normal_user


class CustomerRegisterSerializer(NormalUserRegisterSerializer):
    class Meta(NormalUserRegisterSerializer.Meta):
        pass

    def create(self, validated_data):
        validated_data['role'] = User.UserRole.Customer[0]
        normal_user = super().create(validated_data)
        customer = Customer.objects.create(normal_user=normal_user)
        return customer


class SpecialistRegisterSerializer(NormalUserRegisterSerializer):
    class Meta(NormalUserRegisterSerializer.Meta):
        pass

    def create(self, validated_data):
        validated_data['role'] = User.UserRole.Specialist[0]
        normal_user = super().create(validated_data)
        specialist = Specialist.objects.create(normal_user=normal_user)
        return specialist


class ManagerRegisterSerializer(RegisterSerializer):
    class Meta(RegisterSerializer.Meta):
        pass

    def create(self, validated_data):
        user = super().create(validated_data)
        manager_user = ManagerUser.objects.create(user=user)
        return manager_user


class TechnicalManagerRegisterSerializer(ManagerRegisterSerializer):
    class Meta(ManagerRegisterSerializer.Meta):
        pass

    def create(self, validated_data):
        validated_data['role'] = User.UserRole.TechnicalManager[0]
        manager_user = super().create(validated_data)
        technical_manager = TechnicalManager.objects.create(manager_user=manager_user)
        return technical_manager


class CompanyManagerRegisterSerializer(ManagerRegisterSerializer):
    class Meta(ManagerRegisterSerializer.Meta):
        pass

    def create(self, validated_data):
        validated_data['role'] = User.UserRole.CompanyManager[0]
        manager_user = super().create(validated_data)
        company_manager = CompanyManager.objects.create(manager_user=manager_user)
        return company_manager
