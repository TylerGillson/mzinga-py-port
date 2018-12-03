from MzingaShared.Core.EnumUtils import EnumUtils
from MzingaShared.Core.EnumUtils import PieceNames
from MzingaShared.Core.PiecePositionBase import PiecePositionBase

PassString = "PASS"
_pass = None


class Move(PiecePositionBase):
    _pass = None

    def __init__(self, piece_name=None, position=None, move_string=None):
        if piece_name is None and position is None and move_string is None:
            self.piece_name = list(PieceNames.keys())[0]  # "INVALID"
            self.position = None
        elif move_string is not None:
            if move_string.isspace():
                raise ValueError("Invalid move_string.")
            if not move_string.upper() == PassString:
                self.parse(move_string)
                self.init(self.piece_name, self.position)
        else:
            self.init(piece_name, position)

    def __eq__(self, other):
        if self is None:
            return other is None
        return self.equals(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.get_hash_code()

    def __repr__(self):
        if self.is_pass:
            return PassString
        pos = self.position if self.position else ""
        return "%s[%s]" % (EnumUtils.get_short_name(self.piece_name), str(pos))

    def init(self, piece_name, position):
        if piece_name == list(PieceNames.keys())[0]:  # "INVALID"
            raise ValueError("Invalid piece_name.")
        if position is None:
            raise ValueError("Invalid position.")
        self.piece_name = piece_name
        self.position = position

    def equals(self, move):
        if move is None:
            return False
        return self.piece_name == move.piece_name and self.position == move.position

    @property
    def is_pass(self):
        return self == pass_turn()

    def get_hash_code(self):
        hash_code = 17
        if self.piece_name != list(PieceNames.keys())[0]:  # "INVALID"
            hash_code = hash_code * 31 + int(self.piece_name)
            hash_code = hash_code * 31 + self.position.get_hash_code()
        return hash_code


def pass_turn():
    global _pass
    if _pass:
        return _pass
    else:
        _pass = Move()
        return _pass
