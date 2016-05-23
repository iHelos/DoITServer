# coding=utf-8
import datetime
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from models import Task, WaitConfirm, UserAccount
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

class TaskOutputSerializer(serializers.ModelSerializer):
    #user = UserSerializer(source='user_reciever')
    user = serializers.CharField(source='user_reciever.email')
    hash = serializers.CharField(source='outputHash')

    class Meta:
        model = Task
        fields = ('id', 'name', 'text', 'user', 'date', 'price', 'hash', 'isCompleted')

class TaskInputSerializer(serializers.ModelSerializer):
    #user = UserSerializer(source='user_creator')
    user = serializers.CharField(source='user_creator.email')
    hash = serializers.CharField(source='inputHash')

    class Meta:
        model = Task
        fields = ('id', 'name', 'text', 'user', 'date', 'price', 'hash', 'isCompleted')


class DeviceRegistration(serializers.Serializer):
    email = serializers.EmailField()
    reg_id = serializers.CharField()
    dev_id = serializers.CharField()

    def __init__(self, *args, **kwargs):
        super(DeviceRegistration, self).__init__(*args, **kwargs)

        self.fields['email'].default_error_messages['blank'] = u'0'
        self.fields['email'].default_error_messages['invalid'] = u'1'
        self.fields['email'].default_error_messages['required'] = u'2'

    @transaction.atomic
    def create(self, validated_data):

        email = validated_data['email']
        reg_id = validated_data['reg_id']
        dev_id = validated_data['dev_id']

        password = User.objects.make_random_password()

        user = User.objects.filter(email = email)
        if(len(user) == 0):
            user, userbank = create_user(email, password)

        Device = get_device_model()
        # dev = Device.objects.filter(reg_id = validated_data['reg_id'])
        # dev.delete()
        devices = Device.objects.filter(dev_id = dev_id)
        device = None
        if(len(devices) != 0):
            device = Device.objects.get(dev_id = dev_id)
            device.name = email
            device.reg_id = reg_id
            device.is_active = 0
            device.save()
        else:
            device = Device(
                name = email,
                reg_id = reg_id,
                dev_id = dev_id,
                is_active = 0
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
        device = Device.objects.get(reg_id = reg_id, is_active=1)
        user = User.objects.get(email = device.name)
        return user

class CreateTask(serializers.Serializer):
    title = serializers.CharField()
    text = serializers.CharField()
    price = serializers.IntegerField()
    reciever = serializers.EmailField()
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    day = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        super(CreateTask, self).__init__(*args, **kwargs)

        self.fields['reciever'].default_error_messages['blank'] = u'0'
        self.fields['reciever'].default_error_messages['invalid'] = u'1'
        self.fields['reciever'].default_error_messages['required'] = u'2'
        self.fields['title'].default_error_messages['blank'] = u'0'
        self.fields['title'].default_error_messages['required'] = u'1'
        self.fields['text'].default_error_messages['blank'] = u'0'
        self.fields['text'].default_error_messages['required'] = u'1'
        self.fields['price'].default_error_messages['invalid'] = u'0'
        self.fields['price'].default_error_messages['required'] = u'1'
        self.fields['year'].default_error_messages['invalid'] = u'0'
        self.fields['year'].default_error_messages['required'] = u'1'
        self.fields['month'].default_error_messages['invalid'] = u'0'
        self.fields['month'].default_error_messages['required'] = u'1'
        self.fields['day'].default_error_messages['invalid'] = u'0'
        self.fields['day'].default_error_messages['required'] = u'1'

    @transaction.atomic
    def create(self, validated_data):

        email = validated_data['reciever']
        title = validated_data['title']
        text = validated_data['text']
        price = validated_data['price']
        year = validated_data['year']
        month = validated_data['month']
        day = validated_data['day']

        user_creator = validated_data['owner']

        user = User.objects.get(email = email)
        userbank = UserAccount.objects.get(user_id = user.pk)

        if userbank.bank < price:
            return None, "0"

        date = datetime.date(year, month, day)
        if date < date.today():
            return None, "1"

        userbank.bank-=price
        userbank.save()

        inputHash = 0
        previousInputTask = Task.objects.filter(user_reciever = user).order_by('-id')
        if len(previousInputTask) != 0:
            temp = previousInputTask[0]
            code_text = temp.inputHash + temp.name
            inputHash = java_string_hashcode(code_text)

        outputHash = 0
        previousOutputTask = Task.objects.filter(user_creator = user_creator).order_by('-id')
        if len(previousOutputTask) != 0:
            temp = previousOutputTask[0]
            code_text = temp.outputHash + temp.name
            outputHash = java_string_hashcode(code_text)

        task = Task(name = title, text = text, price = price, user_reciever = user, user_creator = user_creator, isCompleted = 0, date = str(date), inputHash = inputHash, outputHash = outputHash)
        task.save()
        return task, ""

@transaction.atomic
def create_user (email, password = None):
    user = User(
                email=email,
                username=email,
                password=password
            )
    user.save()
    userbank = UserAccount(user = user, bank=1000)
    userbank.save()
    return user, userbank


def java_string_hashcode(s):
    h = 0
    for c in s:
        h = (31 * h + ord(c)) & 0xFFFFFFFF
    return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000