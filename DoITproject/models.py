from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Task(models.Model):
    name = models.TextField()
    text = models.TextField()
    price = models.IntegerField()
    user_creator = models.ForeignKey(User, related_name='creator')
    user_reciever = models.ForeignKey(User, related_name='reciever')
    isCompleted = models.BooleanField()
    date = models.CharField(max_length=10)

    inputHash = models.TextField()
    outputHash = models.TextField()

    def __unicode__(self):
        return self.name

class WaitConfirm(models.Model):
    password = models.TextField()
    devid = models.TextField()

    def __unicode__(self):
        return self.name

class UserAccount(models.Model):
    bank = models.IntegerField()
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.name