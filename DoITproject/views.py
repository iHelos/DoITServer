# coding=utf-8
import traceback

from django.contrib.auth.models import User
from django.core import signing
from django.db import transaction
from django.dispatch import receiver
from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from gcm import signals
from gcm.models import get_device_model
from django.core.signing import Signer
from django.core.mail import send_mail


# Create your views here.
from DoITproject.models import Task, WaitConfirm, UserAccount
from DoITproject.serializers import CreateUserSerializer, DeviceRegistration, GCMToken, CreateTask, TaskInputSerializer, \
    TaskOutputSerializer, TaskResult, TaskCompleted


class SignUp(APIView):
    """
    Регистрация
    """
    throttle_classes = ()
    permission_classes = ()
    # parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    serializer_class = CreateUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
            send_mail('Subject here', 'Here is the message.', 'registration@questmanager.ru',
                      ['ihelos.ermakov@gmail.com'], fail_silently=False)
            return Response({'result': 'check email'})
        except:
            traceback.print_exc()
            raise Http404


sign_up = SignUp.as_view()


class TaskCreate(APIView):
    """
    Создание квеста
    """
    serializer_class = CreateTask

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            task, msg = serializer.save(owner=self.request.user)
            if (task):
                Device = get_device_model()
                device = Device.objects.filter(name=task.user_reciever.email)
                if len(device) == 0:
                    return Response({'detail': 'no devices'}, status=status.HTTP_400_BAD_REQUEST)
                device.send_message(
                    {'type': '1', 'id': task.id, 'title': task.name, 'text': task.text, 'user': task.user_creator.email,
                     'date': task.date, 'price': task.price, 'hash': task.inputHash},
                    delay_while_idle=True
                )
                return Response({'task': task.id, 'hash': task.outputHash})
            else:
                return Response({'task': msg}, status=status.HTTP_400_BAD_REQUEST)
        except:
            traceback.print_exc()
            return Response({'detail': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)


task_create = TaskCreate.as_view()


class TaskInDetail(APIView):
    """
    API получения всех входящих квестов по хэшу
    """

    def get_object(self, hash, user):
        try:
            checkpoint_task = Task.objects.get(user_reciever=user, inputHash=hash)

            return Task.objects.filter(id__gt=checkpoint_task.pk, user_reciever=user), \
                   Task.objects.filter(user_reciever=user, isCompleted=1), \
                   Task.objects.filter(user_reciever=user, isCompleted=-1)

        except Task.DoesNotExist:
            raise Http404

    def get(self, request, hash, format=None):
        task, completed, failed = self.get_object(hash, request.user)
        task = TaskInputSerializer(task, many=True)
        completed = TaskCompleted(completed, many=True)
        failed = TaskCompleted(failed, many=True)
        return Response({
            'tasks': task.data,
            'completed': completed.data,
            'failed': failed.data
        })


class AllTasksInDetail(APIView):
    """
    API получения всех входящих квестов
    """

    def get_objects(self):
        try:
            return Task.objects.filter(user_reciever=self.request.user)
        except Task.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        task = self.get_objects()
        task = TaskInputSerializer(task, many=True)
        return Response({
            'tasks': task.data,
            'completed': [],
            'failed': []
        })


class TaskOutDetail(APIView):
    """
    API получения исходящих квестов по хэшу
    """

    def get_object(self, hash, user):
        try:
            return Task.objects.filter(id__gt=Task.objects.get(user_creator=user, outputHash=hash).pk,
                                       user_creator=user), \
                   Task.objects.filter(user_creator=user, isCompleted=1), \
                   Task.objects.filter(user_creator=user, isCompleted=-1)
        except Task.DoesNotExist:
            raise Http404

    def get(self, request, hash, format=None):
        task, completed, failed = self.get_object(hash, request.user)
        task = TaskOutputSerializer(task, many=True)
        completed = TaskCompleted(completed, many=True)
        failed = TaskCompleted(failed, many=True)
        return Response({
            'tasks': task.data,
            'completed': completed.data,
            'failed': failed.data
        })


class AllTasksOutDetail(APIView):
    """
    API получения всех исходящих квестов
    """

    def get_objects(self):
        try:
            return Task.objects.filter(user_creator=self.request.user)
        except Task.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        task = self.get_objects()
        task = TaskOutputSerializer(task, many=True)
        return Response({
            'tasks': task.data,
            'completed': [],
            'failed': []
        })


class SetResult(APIView):
    """
    Регистрация устройства
    """
    serializer_class = TaskResult

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            devices, task = serializer.save(owner=request.user)
            devices.send_message(
                {'type': '2', 'id': task.id, 'isCompleted': task.isCompleted},
                delay_while_idle=True
            )
            return Response({
                'result': task.isCompleted
            })
        except:
            traceback.print_exc()
            raise Http404


set_result = SetResult.as_view()

# @receiver(signals.device_registered)
# def my_callback(sender, **kwargs):
#     print("Request finished!")

class DeviceRegistrationView(APIView):
    """
    Регистрация устройства
    """
    throttle_classes = ()
    permission_classes = ()
    serializer_class = DeviceRegistration

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            password, device = serializer.save()
            # if created:
            value = signing.dumps({device.dev_id: password})

            confirm_url = 'https://api.questmanager.ru/confirm/?pass={}'.format(value)
            send_mail('Регистрация QuestManager',
                      'Ура, Вам остался всего лишь один шаг для подтверждения Вашего устройства - '
                      'перейдите по данной ссылке:\n {}'.format(confirm_url),
                      'registration@questmanager.ru',
                      [device.name], fail_silently=False)
            # else:
            #     value = signing.dumps({reg_id: password})
            #
            #     confirm_url = 'https://api.questmanager.ru/confirm/?pass={}'.format(value)
            #     send_mail('Регистрация QuestManager',
            #               'Ура, Вам остался всего лишь один шаг для подтверждения Вашего устройства - '
            #               'перейдите по данной ссылке:\n {}'.format(confirm_url),
            #               'registration@questmanager.ru',
            #      [email], fail_silently=False)

        except:
            traceback.print_exc()
            raise Http404
        return Response({'result': 'check email'})


device_register = DeviceRegistrationView.as_view()


class GetAuthTokenView(APIView):
    """
    Регистрация устройства
    """
    throttle_classes = ()
    permission_classes = ()
    serializer_class = GCMToken

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
            userBank = UserAccount.objects.get(user=user)
            token = Token.objects.get_or_create(user=user)[0]
            return Response({
                'token': token.key,
                'bank': userBank.bank
            })
        except:
            traceback.print_exc()
            raise Http404


auth_token = GetAuthTokenView.as_view()


@transaction.atomic
def confirm_registration(request):
    try:
        signer = Signer()
        password = request.GET['pass']
        secret = signing.loads(password)
        dev_id, password = secret.items()[0]

        confirm = WaitConfirm.objects.get(devid=dev_id, password=password)
        Device = get_device_model()
        device = Device.objects.get(dev_id=dev_id)
        device.is_active = True
        device.save()

        confirm.delete()

        user = User.objects.get(email=device.name)
        userbank = UserAccount.objects.get(user=user)
        token = Token.objects.get_or_create(user=user)[0]

        asd = device.send_message(
            {'type': '0', 'message': 'Ваше устройство успешно подтверждено!', 'auth_token': token.key,
             'bank': userbank.bank}, delay_while_idle=True)
        print(asd)
        return HttpResponse('good')
    except:
        return HttpResponse(traceback.format_exc())


@receiver(signals.device_registered)
def my_callback(sender, device, request, **kwargs):
    Device = get_device_model()
    print(sender)
    print(device)
    print(request)
    print("Request finished!")
