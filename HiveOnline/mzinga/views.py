from django.core.exceptions import ObjectDoesNotExist, ValidationError
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


# Send an email update to a game's human player:
def notify_player_turn(g, recipient=None):
    recipient_email = recipient if recipient else g.player_1.email
    send_mail(
        'HiveOnline - Game ID: ' + str(g.id),
        'The ball is in your court!\n\nGame ID: %s\n\nBoard String: %s\n\nCurrent Turn: %s'
        % (str(g.id), g.board_string, g.current_turn.name),
        'noreply@hiveonline.com',
        [recipient_email],
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
    http_method_names = ['get', 'delete']

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
        Expected request body:
            {
                "colour": ['Black', 'White'],         (Initiating player colour)
                "opponent": ['AI', '<email>'],        ('AI', or specify opponent email)
                "ai_config": ["time 10", "depth 1"]   (AI turn timeout, or search max depth)
            }
        :return: JSON serialization of newly created game
        """
        # Extract args from request body:
        colour = request.data['colour']
        opponent = request.data['opponent']
        ai_config = request.data['ai_config']

        # Init game, then add players:
        g = Game()
        g.player_1 = request.user
        if opponent == 'AI':
            g.player_2 = User.objects.get_by_natural_key(opponent)

        # Initiator plays first:
        if colour == 'White':
            g.status = 'NotStarted'
            g.board_string = g.status + ";White[1]"
            g.current_turn = g.player_1
            notify_player_turn(g)

        # Opponent plays first:
        elif colour == 'Black':
            engine.parse_command("newgame")

            # If playing AI, calculate, then play best move according to ai_config:
            if opponent == 'AI':
                best_move = engine.parse_command("bestmove " + ai_config)
                g.board_string = engine.parse_command("play " + str(best_move))
                g.status = 'InProgress'
                g.current_turn = g.player_1
                notify_player_turn(g)

            # Otherwise, notify opponent:
            else:
                send_mail(
                    'HiveOnline - Game ID: ' + str(g.id),
                    'You\'ve been invited to a game of Hive.\n\nPOST to: /hive-online/join_game/ with JSON content: \
                        {"game_id": "' + str(g.id) + '"} to join.',
                    'noreply@hiveonline.com',
                    [opponent],
                )

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
            - game_id: UUID of the game session you are playing to
            - move: A move string representing the desired move, i.e., "WB1[0,0,0]"

        :param request: an HTTP request object
        :return: JSON serialization of updated game
        """
        move_str = request.data['move']
        game_id = request.data['game_id']

        # Perform validation:
        try:
            g = Game.objects.get(id=game_id)
        except ValidationError or ObjectDoesNotExist:
            return Response({'ERROR': 'Invalid game_id.'}, status=status.HTTP_404_NOT_FOUND)
        if g.current_turn != request.user:
            return Response({'ERROR': 'It is not your turn!'}, status=status.HTTP_403_FORBIDDEN)

        # Load game & play move:
        engine.parse_command("newgame " + g.board_string)
        g.board_string = engine.parse_command("play " + move_str)

        # Update turn & send notification:
        g.current_turn = g.player_1 if g.current_turn == g.player_2 else g.player_2
        notify_player_turn(g, g.current_turn.email)

        # Return updated game:
        serializer = GameSerializer(g, many=False, context={'request': request})
        return Response(serializer.data)


class JoinGame(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def create(request):
        """
        Join an existing game of Hive.

        Args:
            - game_id: UUID of the game session you wish to join

        :param request: an HTTP request object
        :return: JSON serialization of updated game
        """
        game_id = request.data['game_id']

        # Perform validation:
        try:
            g = Game.objects.get(id=game_id)
        except ValidationError or ObjectDoesNotExist:
            return Response({'ERROR': 'Invalid game_id'}, status=status.HTTP_404_NOT_FOUND)
        if g.player_2 is not None:
            return Response({'ERROR': 'Game already has two players!'}, status=status.HTTP_403_FORBIDDEN)

        # Update game:
        g.player_2 = request.user
        g.save()

        # Notify opponent:
        send_mail(
            'HiveOnline - Game ID: ' + str(g.id),
            'Your opponent has joined the game!\n\nGame ID: %s\n\nBoard String: %s\n\nCurrent Turn: %s'
            % (str(g.id), g.board_string, g.current_turn.name),
            'noreply@hiveonline.com',
            [g.player_1.email],
        )

        # Return updated game:
        serializer = GameSerializer(g, many=False, context={'request': request})
        return Response(serializer.data)
