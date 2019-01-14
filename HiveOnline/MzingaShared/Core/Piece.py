from MzingaShared.Core.PiecePositionBase import PiecePositionBase


class Piece(PiecePositionBase):
    __slots__ = "piece_above", "piece_below"

    @property
    def in_play(self):
        return self.position is not None

    @property
    def in_hand(self):
        return self.position is None

    def __init__(self, piece_name, position=None, piece_string=None):
        super().__init__()
        self.piece_above = None
        self.piece_below = None
        self.position = None
        self.piece_name = "INVALID"

        if piece_string:
            if piece_string.isspace():
                raise ValueError("Invalid piece_string.")
            self.parse(piece_string)
            self.init(self.piece_name, self.position)
        else:
            self.init(piece_name, position)

    def init(self, piece_name, position):
        if piece_name == "INVALID":
            raise ValueError("Invalid piece_name.")
        self.piece_name = piece_name
        self.position = position

    def move(self, new_position):
        self.position = new_position
