from MzingaShared.Core.EnumUtils import EnumUtils
from MzingaShared.Core.PiecePositionBase import PiecePositionBase

pass_string = "PASS"
_pass = None


class Move(PiecePositionBase):
    __slots__ = "_pass"

    @property
    def is_pass(self):
        return self == pass_turn()

    def __init__(self, piece_name=None, position=None, move_string=None):
        super().__init__()
        self._pass = None

        if piece_name is None and position is None and move_string is None:
            self.piece_name = "INVALID"
            self.position = None

        elif move_string is not None:
            if move_string.isspace():
                raise ValueError("Invalid move_string.")
            if not move_string.upper() == pass_string:
                self.parse(move_string)
                self.init(self.piece_name, self.position)
        else:
            self.init(piece_name, position)

    def __eq__(self, other):
        return other is None if self is None else self.equals(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.get_hash_code()

    def __repr__(self):
        if self.is_pass:
            return pass_string

        pos = self.position if self.position else ""
        return "%s[%s]" % (EnumUtils.get_short_name(self.piece_name), str(pos))

    def init(self, piece_name, position):
        if piece_name == "INVALID":
            raise ValueError("Invalid piece_name.")
        if position is None:
            raise ValueError("Invalid position.")

        self.piece_name = piece_name
        self.position = position

    def equals(self, move):
        return False if move is None else self.piece_name == move.piece_name and self.position == move.position

    def get_hash_code(self):
        hash_code = 17
        if self.piece_name != "INVALID":
            hash_code = hash_code * 31 + hash(self.piece_name)
            hash_code = hash_code * 31 + self.position.get_hash_code()
        return hash_code


def pass_turn():
    global _pass
    if _pass:
        return _pass
    else:
        _pass = Move()
        return _pass
