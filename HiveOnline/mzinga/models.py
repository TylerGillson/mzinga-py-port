import uuid
from django.db import models
from django.contrib.auth.models import User


class Game(models.Model):
    id = models.UUIDField(default=uuid.uuid4(), editable=False, unique=True, primary_key=True)
    player_1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='p1')
    player_2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='p2', null=True)
    current_turn = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    ai_config = models.CharField(max_length=16, null=True)
    status = models.CharField(max_length=16)
    board_string = models.CharField(default=None, max_length=2048)
    objects = models.Manager()
