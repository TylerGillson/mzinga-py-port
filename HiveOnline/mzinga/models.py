import uuid
from django.db import models
from django.contrib.auth.models import User


class Game(models.Model):
    id = models.UUIDField(default=uuid.uuid4(), editable=False, unique=True, primary_key=True)
    player_1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='p1')
    player_2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='p2')
    status = models.CharField(max_length=16)
    objects = models.Manager()