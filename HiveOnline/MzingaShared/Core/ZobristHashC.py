import pyximport
pyximport.install(language_level=3)
from MzingaShared.Core import ZobristHelper

from MzingaShared.Core import Position, EnumUtils
from MzingaShared.Core.EnumUtils import PieceNames

NumUniquePositions = Position.MaxStack * EnumUtils.NumPieceNames * EnumUtils.NumPieceNames


class ZobristHashC:
    Value = None
    _next = 1
    _hashPartByPosition = None
    _hashPartByLastMovedPiece = None
    _hashPartByTurnColor = None

    def __init__(self):
        ZobristHelper.init(self, Position.get_unique_positions(NumUniquePositions), EnumUtils.NumPieceNames)

    def toggle_piece(self, piece_name, position):
        self.Value ^= self._hashPartByPosition[EnumUtils.PieceNames[piece_name]][position]

    def toggle_last_moved_piece(self, piece_name):
        if piece_name != list(PieceNames.keys())[0]:  # "INVALID"
            self.Value ^= self._hashPartByLastMovedPiece[piece_name]

    def toggle_turn(self):
        self.Value ^= self._hashPartByTurnColor
