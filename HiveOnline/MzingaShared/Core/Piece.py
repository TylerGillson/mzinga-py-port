from MzingaShared.Core.EnumUtils import PieceNames
from MzingaShared.Core.PiecePositionBase import PiecePositionBase


class Piece(PiecePositionBase):
    piece_above = None
    piece_below = None

    @property
    def in_play(self):
        return self.position is not None

    @property
    def in_hand(self):
        return self.position is None

    def __init__(self, piece_name, position=None, piece_string=None):
        self.piece_name = list(PieceNames.keys())[0]  # "INVALID"
        self.position = None

        if piece_string:
            if piece_string.isspace():
                raise ValueError("Invalid piece_string.")
            self.parse(piece_string)
            self.init(self.piece_name, self.position)
        else:
            self.init(piece_name, position)

    def init(self, piece_name, position):
        if piece_name == list(PieceNames.keys())[0]:  # "INVALID"
            raise ValueError("Invalid piece_name.")
        self.piece_name = piece_name
        self.position = position

    def move(self, new_position):
        self.position = new_position
