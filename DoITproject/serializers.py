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

    @transaction.atomic
    def create(self, validated_data):
        Device = get_device_model()
        device = Device(
            name = validated_data['email'],
            reg_id = validated_data['reg_id'],
            dev_id = validated_data['reg_id']
        )
        device.save()

        password = User.objects.make_random_password()

        waitConfirm = WaitConfirm(
            devid = device.dev_id,
            password = password
        )
        waitConfirm.save()
        return password, device.dev_id