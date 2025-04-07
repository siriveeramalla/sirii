from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_rooms")
    password = models.CharField(max_length=255)  # Password for the room
    participants = models.ManyToManyField(User, related_name="rooms", blank=True)
    content = models.TextField(default="")  
class UserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_logged_in = models.BooleanField(default=False)
class LoggedInUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    def __str__(self):
        return self.name
