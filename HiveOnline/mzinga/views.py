from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . serializers import UserSerializer, GameSerializer
from . models import Game

from MzingaShared.Engine import GameEngineConfig
from MzingaShared.Engine.GameEngine import GameEngine

engine = GameEngine("HiveOnline", GameEngineConfig.get_default_config())


# Notify Human player:
def notify_human_player(g):
    send_mail(
        'HiveOnline - Game ID:' + str(g.id),
        'The ball is in your court!\n\nGame ID: %s\n\nBoard String: %s' % (str(g.id), g.board_string),
        'noreply@hiveonline.com',
        [g.player_1.email],
    )


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GameViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows games to be viewed or edited.
    """
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    def get_queryset(self):
        return Game.objects.all()

    def list(self, request, *args, **kwargs):
        serializer = GameSerializer(self.get_queryset(), many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        g = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = GameSerializer(g, many=False, context={'request': request})
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        g = get_object_or_404(self.get_queryset(), pk=pk)
        self.perform_destroy(g)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NewGame(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def create(request):
        """
        Initiate a new game of Hive.

        :param request: an HTTP request object
        :param kwargs: {
            "colour": ['Black', 'White'],
            "ai_config": ["time 10", "depth 1"]
        }
        :return: JSON serialization of newly created game
        """
        # Init game, then add players:
        g = Game()
        g.player_1 = request.user
        g.player_2 = User.objects.get_by_natural_key("AI")

        # Extract args from request body:
        ai_config = request.data['ai_config']
        colour = request.data['colour']

        # AI plays first --> calculate, then play best move according to ai_config:
        if colour == 'Black':
            engine.parse_command("newgame")
            best_move = engine.parse_command("bestmove " + ai_config)
            g.board_string = engine.parse_command("play " + str(best_move))
            g.status = 'InProgress'
            notify_human_player(g)

        # Human plays first --> init game:
        elif colour == 'White':
            g.status = 'NotStarted'
            g.board_string = g.status + ";White[1]"
            notify_human_player(g)

        # Save model instance & return serialized data:
        g.save()
        serializer = GameSerializer(g, many=False, context={'request': request})
        return Response(serializer.data)


class PlayMove(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def create(request):
        """
        Play a turn on an existing game of Hive.

        Args:
            - game_id: The ID of the game session you are playing on, i.e., "1"
            - move: A move string representing the desired move, i.e., "WB1[0,0,0]"

        :param request: an HTTP request object
        :return: JSON serialization of updated game
        """
        move_str = request.data['move']
        game_id = request.data['game_id']

        try:
            g = Game.objects.get(id=game_id)
        except ObjectDoesNotExist:
            return get_object_or_404(Game, name="game")

        engine.parse_command("newgame " + g.board_string)  # Load game from board_string
        g.board_string = engine.parse_command("play " + move_str)  # Get updated board_string

        # Do turn notifications

        # Return updated game:
        serializer = GameSerializer(g, many=False, context={'request': request})
        return Response(serializer.data)

# Common Functionality:
#   - Start game (choose Black or White)
#   - Play move (including turn & end game notifications)
#   - End game notifications
