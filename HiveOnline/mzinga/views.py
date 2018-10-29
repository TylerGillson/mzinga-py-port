from django.contrib.auth.models import User

from rest_framework import viewsets
from rest_framework.views import APIView

from . serializers import UserSerializer, GameSerializer
from . models import Game


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
        pass

    def create(self, request, *args, **kwargs):
        """
        Initiate a new game of Hive.
        :param request: an HTTP request object
        :param args: None
        :param kwargs: {
            'colour'=['Black', 'White'],
            'p2p'=[True, False]
        }
        :return: a unique game URI
        """
        g = Game()
        g.status = 'NotStarted'
        g.player_1 = request.user.id
        p2p = kwargs.get('p2p')
        colour = kwargs.get('colour')

        # AI plays first:
        if p2p == 'False' and colour == 'Black':
            pass
        # Human plays first:
        elif p2p == 'False' and colour == 'White':
            pass

        # P2P initiator plays first:
        if p2p == 'True' and colour == 'White':
            pass
        # P2P initiator plays second:
        elif p2p == 'True' and colour == 'Black':
            pass

        return g.id


class PlayMove(APIView):

    def post(self, *args, **kwargs):
        """
        """
        move = kwargs.get('move')
        game_id = kwargs.get('game_id')

        def play_move(session, move_string):
            return move_string

        def load_game(board_string):
            return board_string

        game = Game.objects.get(id=game_id)
        session = load_game(game.board_string)
        play_move(session, move)
        game.board_string = session.get_board_string()

        # Do turn notifications

# Common Functionality:
#   - Start game (choose Black or White)
#   - Play move (including turn & end game notifications)
#   - End game notifications

# P2P Functionality:
#   - Share game (export game URI)

# PVC Functionality:
#   - Configure AI search parameters
