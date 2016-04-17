# coding=utf-8
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from models import Task


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
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