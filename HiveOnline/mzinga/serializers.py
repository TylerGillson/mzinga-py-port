from django.contrib.auth.models import User

from rest_framework import serializers

from . models import Game


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GameSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Game
        fields = ('id', 'player_1', 'player_2', 'status', 'board_string')
