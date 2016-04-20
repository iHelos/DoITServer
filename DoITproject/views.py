# coding=utf-8
import traceback
from django.core import signing
from django.dispatch import receiver
from django.http import  Http404, HttpResponse
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from gcm import signals
from gcm.models import get_device_model
from django.core.signing import Signer

from django.core.mail import EmailMessage, send_mail

# Create your views here.
from DoITproject.models import Task, WaitConfirm
from DoITproject.serializers import UserSerializer, GroupSerializer, CreateUserSerializer, CreateTaskSerializer, \
    DeviceRegistration


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
    serializer_class = CreateTaskSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=self.request.user)
        return Response({'task': serializer.data})
task_create = TaskCreate.as_view()

class TaskInDetail(APIView):
    """
    API получения одного входящих квестов
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
    API получения всех входящих квестов
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
    API получения конкретного исходящего квеста
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
    API получения всех исходящих квестов
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
            password, dev_id = serializer.save()
            value = signing.dumps({dev_id: password})

            confirm_url = 'https://api.questmanager.ru/confirm/?pass={}'.format(value)
            send_mail('Регистрация QuestManager',
                      'Ура, Вам остался всего лишь один шаг для подтверждения Вашего устройства - '
                      'перейдите по данной ссылке:\n {}'.format(confirm_url),
                      'registration@questmanager.ru',
             ['ihelos.ermakov@gmail.com'], fail_silently=False)
        except:
            return Response({'result': 'error'})
        return Response({'result': 'check email'})
device_register = DeviceRegistrationView.as_view()

def confirm_registration(request):
    try:
        signer = Signer()
        password = request.GET['pass']
        secret = signing.loads(password)
        dev_id, password = secret.items()[0]
        confirm = WaitConfirm.objects.get(devid = dev_id, password = password)
        Device = get_device_model()
        device = Device.objects.get(dev_id= dev_id)
        device.is_active = 1
        device.save()
        device.send_message({'message':'Ваше устройство успешно подтверждено!'}, delay_while_idle=True)
        return HttpResponse('good')
    except:
        return HttpResponse('fuck')

@receiver(signals.device_registered)
def my_callback(sender, device, request, **kwargs):
    Device = get_device_model()
    print(sender)
    print(device)
    print(request)
    print("Request finished!")