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

    def __unicode__(self):
        return self.name
