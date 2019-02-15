from MzingaShared.Core import Move, EnumUtils, NotationUtils
from MzingaShared.Core.Board import Board, InvalidMoveException
from MzingaShared.Core.BoardHistory import BoardHistory
from Utils.Events import Broadcaster


class GameBoard(Board):
    board_changed = Broadcaster()

    def on_board_changed(self):
        white_queen_surrounded = self.count_neighbors(piece_name="WhiteQueenBee")[0] == 6
        black_queen_surrounded = self.count_neighbors(piece_name="BlackQueenBee")[0] == 6

        if white_queen_surrounded and black_queen_surrounded:
            self.board_state = "Draw"
        elif white_queen_surrounded:
            self.board_state = "BlackWins"
        elif black_queen_surrounded:
            self.board_state = "WhiteWins"
        else:
            self.board_state = "NotStarted" if self.current_turn == 0 else "InProgress"

    board_changed.on_change += on_board_changed  # add a listener to the event

    @property
    def board_history_count(self):
        return self._board_history.count

    @property
    def board_history(self):
        return self._board_history

    @board_history.setter
    def board_history(self, value):
        self._board_history = value

    @property
    def last_move(self):
        return self._board_history.last_move

    def __init__(self, board_string=None, game_type=None, **kwargs):
        self.board_history = BoardHistory()
        self.last_piece_moved = None
        self.board_state = None

        super().__init__(board_string=board_string, game_type=game_type, **kwargs)

    def __repr__(self):
        return super().__repr__()

    def clone(self):
        clone = GameBoard(board_string="START", game_type=self.game_type)
        for item in self.board_history:
            clone.trusted_play(item.move, item.move_string)
        return clone

    def play(self, move, move_string=None):
        if move is None:
            raise ValueError("Invalid move.")
        if move.is_pass:
            self.pass_turn()
            return
        if self.game_is_over:
            raise ValueError("You can't play, the game is over.")

        valid_moves = self.get_valid_moves()
        if not valid_moves.contains(move):
            if move.colour != self.current_turn_colour:
                raise InvalidMoveException(move, "It's not that player's turn.")

            if move.position is None:
                raise InvalidMoveException(move, "You can't put a piece back into your hand.")

            if self.current_player_turn == 1 and move.bug_type == "QueenBee":
                raise InvalidMoveException(move, "You can't play your Queen Bee on your first turn.")

            target_piece = self.get_piece(move.piece_name)
            if not self.current_turn_queen_in_play:
                if self.current_player_turn == 4 and target_piece.bug_type != "QueenBee":
                    raise InvalidMoveException(move, "You must play your Queen Bee on or before your fourth turn.")
                elif target_piece.in_play:
                    raise InvalidMoveException(
                        move, "You can't move a piece in play until you've played your Queen Bee.")

            if not self.placing_piece_in_order(target_piece):
                raise InvalidMoveException(
                    move, "When there are multiple pieces of the same bug type, you must play the pieces in order.")
            if self.has_piece_at(move.position):
                raise InvalidMoveException(
                    move, "You can't move there because a piece already exists at that position.")

            if target_piece.in_play:
                if target_piece.position == move.position:
                    raise InvalidMoveException(move, "You can't move a piece to its current position.")
                elif not self.piece_is_on_top(target_piece):
                    raise InvalidMoveException(move, "You can't move that piece because it has a beetle on top of it.")
                elif not self.can_move_without_breaking_hive(target_piece):
                    raise InvalidMoveException(move, "You can't move that piece because it will break the hive.")

            raise InvalidMoveException(move)

        if move_string is not None:
            play_str = NotationUtils.normalize_boardspace_move_string(move_string)
        else:
            play_str = NotationUtils.to_boardspace_move_string(self, move)

        self.trusted_play(move, play_str)

    def pass_turn(self):
        pass_turn = Move.pass_turn()

        if self.game_is_over:
            raise InvalidMoveException(pass_turn, "You can't pass, the game is over.")

        if pass_turn not in self.get_valid_moves():
            raise InvalidMoveException(pass_turn, "You can't pass when you have valid moves.")

        self.trusted_play(pass_turn, NotationUtils.boardspace_pass)

    def trusted_play(self, move, move_string=None):
        original_position = None

        if not move.is_pass:
            target_piece = self.get_piece(move.piece_name)
            original_position = target_piece.position
            self.move_piece(target_piece, move.position)

        self._board_history.add(move, original_position, move_string)
        self.current_turn += 1
        self.last_piece_moved = move.piece_name
        self.board_changed.on_change.fire(self)  # fire event

    def undo_last_move(self):
        if self._board_history.count == 0:
            raise InvalidMoveException("You can't undo any more moves.")

        item = self._board_history.undo_last_move()
        if not item.move.is_pass:
            target_piece = self.get_piece(item.move.piece_name)
            self.move_piece(target_piece, item.original_position)

        previous_move = self._board_history.last_move
        if previous_move:
            previous_move = previous_move.move
            self.last_piece_moved = previous_move.piece_name
        else:
            self.last_piece_moved = "INVALID"

        self.current_turn -= 1
        self.board_changed.on_change.fire(self)

    def to_game_string(self):
        game_strs = []
        game_strs.extend([self.board_state, ';'])  # board state
        game_strs.append("".join([self.current_turn_colour, str(self.current_player_turn), ';']))  # turn state

        # moves:
        for item in self.board_history.get_enumerator:
            if item.move_string:
                move_str = item.move_string
            else:
                move_str = NotationUtils.to_boardspace_move_string(self, item.move)
            game_strs.append("%s%c" % (move_str, ';'))

        return "".join(game_strs)[0:-1]


def try_parse_game_string(game_string, game_type):
    try:
        board = parse_game_string(game_string, game_type)
        return True, board
    except ValueError or Exception:
        return False, None


def parse_game_string(game_string, game_type):
    if game_string is None or game_string.isspace():
        raise ValueError("Invalid game_string.")

    split = game_string.split(';')
    gb = GameBoard("START", game_type)
    normalized_move_strs = list(map(NotationUtils.normalize_boardspace_move_string, split[3:]))

    for nms in normalized_move_strs:
        move = NotationUtils.parse_move_string(gb, nms)
        gb.play(move, nms)

    return gb
