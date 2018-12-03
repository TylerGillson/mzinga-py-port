from django.contrib.auth.models import User

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from . serializers import UserSerializer, GameSerializer
from . models import Game

from HiveOnline.MzingaShared.Engine import GameEngineConfig
from HiveOnline.MzingaShared.Engine.GameEngine import GameEngine


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

    def list(self, request, *args, **kwargs):
        serializer = GameSerializer(self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Initiate a new game of Hive.
        :param request: an HTTP request object
        :param args: None
        :param kwargs: {
            'colour'=['Black', 'White'],
            'ai_config'=["max_time 10", "max_depth 1"]
        }
        :return: a unique game URI
        """
        g = Game()
        g.player_1 = request.user.id
        g.player_2 = User.objects.get_by_natural_key("ai")
        g.status = 'NotStarted'

        ai_config = kwargs.get('ai_config')
        colour = kwargs.get('colour')

        # AI plays first:
        if colour == 'Black':
            config = GameEngineConfig.get_default_config()
            engine = GameEngine("HiveOnline", config)
            engine.parse_command("newgame")
            best_move = engine.parse_command("bestmove " + ai_config)
            g.board_string = engine.parse_command("play " + best_move)

        # Human plays first:
        elif colour == 'White':
            g.board_string = g.status + ";White[1]"

        serializer = GameSerializer(g, many=False)
        return Response(serializer.data)


class PlayMove(APIView):

    def __init__(self):
        super().__init__()
        config = GameEngineConfig.get_default_config()
        self.engine = GameEngine("HiveOnline", config)

    def play_move(self, session, move_string):
        return move_string

    def load_game(self, board_string):
        return self.engine.parse_command("newgame " + board_string)

    def post(self, **kwargs):
        """
        """
        move = kwargs.get('move')
        game_id = kwargs.get('game_id')

        game = Game.objects.get(id=game_id)
        session = self.load_game(game.board_string)
        self.play_move(session, move)
        game.board_string = session.get_board_string()

        # Do turn notifications

# Common Functionality:
#   - Start game (choose Black or White)
#   - Play move (including turn & end game notifications)
#   - End game notifications
