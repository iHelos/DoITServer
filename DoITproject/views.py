# coding=utf-8
from xml import parsers
from django.contrib.auth.models import User, Group
from django.core import mail
from django.http import JsonResponse, Http404
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.mail import EmailMessage, send_mail

# Create your views here.
from DoITproject.models import Task
from DoITproject.serializers import UserSerializer, GroupSerializer, CreateUserSerializer, CreateTaskSerializer

class SignUp(APIView):
    """
    Регистрация
    """
    throttle_classes = ()
    permission_classes = ()
    # parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    serializer_class = CreateUserSerializer
    def post(self, request, *args, **kwargs):
        send_mail('Subject here', 'Here is the message.', 'registration@questmanager.ru',
             ['ihelos.ermakov@gmail.com'], fail_silently=False)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'token': Token.objects.create(user = serializer.save()).key})
sign_up = SignUp.as_view()

class TaskCreate(APIView):
    """
    Создание квеста
    """
    serializer_class = CreateTaskSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=self.request.user)
        return Response({'task': serializer.data})
task_create = TaskCreate.as_view()

class TaskInDetail(APIView):
    """
    API получения юзеров
    """
    def get_object(self, pk):
        try:
            return Task.objects.get(pk=pk, user_reciever = self.request.user)
        except Task.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        task = self.get_object(pk)
        task = CreateTaskSerializer(task)
        return Response(task.data)


class AllTasksInDetail(APIView):
    """
    API получения юзеров
    """
    def get_objects(self):
        try:
            return Task.objects.filter(user_reciever = self.request.user)
        except Task.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        task = self.get_objects()
        task = CreateTaskSerializer(task, many=True)
        return Response(task.data)

class TaskOutDetail(APIView):
    """
    API получения юзеров
    """
    def get_object(self, pk):
        try:
            return Task.objects.get(pk=pk, user_creator = self.request.user)
        except Task.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        task = self.get_object(pk)
        task = CreateTaskSerializer(task)
        return Response(task.data)


class AllTasksOutDetail(APIView):
    """
    API получения юзеров
    """
    def get_objects(self):
        try:
            return Task.objects.filter(user_creator = self.request.user)
        except Task.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        task = self.get_objects()
        task = CreateTaskSerializer(task, many=True)
        return Response(task.data)