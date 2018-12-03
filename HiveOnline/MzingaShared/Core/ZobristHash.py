from MzingaShared.Core import Position, EnumUtils
from MzingaShared.Core.EnumUtils import PieceNames

EmptyBoard = 0
NumUniquePositions = Position.MaxStack * EnumUtils.NumPieceNames * EnumUtils.NumPieceNames

hash_part_by_turn_colour = None
hash_part_by_last_moved_piece = None
hash_part_by_position = None


class ZobristHash:
    Value = None
    _next = 1

    def rand_64(self):
        self._next = self._next * 1103515245 + 12345
        return self._next

    def __init__(self):
        self.Value = EmptyBoard

        # Only compute hash tables once:
        global hash_part_by_turn_colour, hash_part_by_last_moved_piece, hash_part_by_position
        if hash_part_by_turn_colour is None:
            self._hashPartByTurnColor = self.rand_64()
            self._hashPartByLastMovedPiece = [0] * EnumUtils.NumPieceNames
            self._hashPartByPosition = {}

            for i in range(EnumUtils.NumPieceNames):
                self._hashPartByLastMovedPiece[i] = self.rand_64()

            unique_positions = Position.get_unique_positions(NumUniquePositions)

            for i in range(EnumUtils.NumPieceNames):
                self._hashPartByPosition[i] = {}

                for pos in unique_positions:
                    self._hashPartByPosition[i][pos] = self.rand_64()

            hash_part_by_turn_colour = self._hashPartByTurnColor
            hash_part_by_last_moved_piece = self._hashPartByLastMovedPiece
            hash_part_by_position = self._hashPartByPosition
        else:
            self._hashPartByTurnColor = hash_part_by_turn_colour
            self._hashPartByLastMovedPiece = hash_part_by_last_moved_piece
            self._hashPartByPosition = hash_part_by_position

    def toggle_piece(self, piece_name, position):
        self.Value ^= self._hashPartByPosition[EnumUtils.PieceNames[piece_name]][position]

    def toggle_last_moved_piece(self, piece_name):
        if piece_name != list(PieceNames.keys())[0]:  # "INVALID"
            self.Value ^= self._hashPartByLastMovedPiece[piece_name]

    def toggle_turn(self):
        self.Value ^= self._hashPartByTurnColor
