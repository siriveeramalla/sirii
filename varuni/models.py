from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_rooms")
    password = models.CharField(max_length=255)
    participants = models.ManyToManyField(User, related_name="rooms", blank=True)

    def __str__(self):
        return self.name

class UserStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_logged_in = models.BooleanField(default=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} in {self.room.name}"

class RoomContent(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE)
    content = models.TextField(blank=True)

    def __str__(self):
        return f"Content for {self.room.name}"
