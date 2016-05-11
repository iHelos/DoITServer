# coding=utf-8
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from models import Task, WaitConfirm
from gcm.models import get_device_model
from django.db import transaction


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email',)
        extra_kwargs = {'email': {'required': True}}

    def create(self, validated_data):
        email = validated_data['email']
        user = User.objects.filter(username=email)

        if not user.exists():
            user = User(
                email=email,
                username=email
            )
            user.set_password(User.objects.make_random_password())
            user.save()
        else:
            user = user[0]
        return user

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)

class CreateTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('name', 'text', 'price', 'user_reciever')

    def create(self, validated_data):
        task = Task(
            name = validated_data['name'],
            text = validated_data['text'],
            price = validated_data['price'],
            user_reciever = validated_data['user_reciever'],
            user_creator = validated_data['owner'],
            isCompleted = False
        )
        task.save()
        return task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('user_reciever', 'text', 'price')

class DeviceRegistration(serializers.Serializer):
    email = serializers.EmailField()
    reg_id = serializers.CharField()
    dev_id = serializers.CharField()

    @transaction.atomic
    def create(self, validated_data):

        email = validated_data['email']
        reg_id = validated_data['reg_id']
        dev_id = validated_data['dev_id']

        password = User.objects.make_random_password()

        user = User.objects.filter(email = email)
        if(len(user) == 0):
            newUser = User(email=email, password = password, username = email)
            newUser.save()

        Device = get_device_model()
        # dev = Device.objects.filter(reg_id = validated_data['reg_id'])
        # dev.delete()
        devices = Device.objects.filter(dev_id = dev_id)
        device = None
        if(len(devices) != 0):
            device = Device.objects.get(reg_id = reg_id)
            device.name = email
            device.save()
        else:
            device = Device(
                name = email,
                reg_id = reg_id,
                dev_id = reg_id
            )
            device.save()

        waitConfirm = WaitConfirm(
            devid = dev_id,
            password = password
        )
        waitConfirm.save()
        return password, device

class GCMToken(serializers.Serializer):
    reg_id = serializers.CharField()

    @transaction.atomic
    def create(self, validated_data):
        Device = get_device_model()
        reg_id = validated_data['reg_id']
        device = Device.objects.get(reg_id = reg_id)
        user = User.objects.get(email = device.name)
        return user