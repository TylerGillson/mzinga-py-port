from MzingaShared.Core import Position
from MzingaShared.Core.EnumUtils import PieceNames, NumPieceNames

EmptyBoard = 0
NumUniquePositions = Position.MaxStack * NumPieceNames * NumPieceNames

hash_part_by_turn_colour = None
hash_part_by_last_moved_piece = None
hash_part_by_position = None


class ZobristHash(object):
    __slots__ = "value", "_next", \
                "_hash_part_by_turn_colour", \
                "_hash_part_by_last_moved_piece", \
                "_hash_part_by_position"

    def rand_64(self):
        self._next = self._next * 1103515245 + 12345
        return self._next

    def __init__(self):
        self.value = EmptyBoard
        self._next = 1

        # Only compute hash tables once:
        global hash_part_by_turn_colour, hash_part_by_last_moved_piece, hash_part_by_position

        if hash_part_by_turn_colour is None:
            self._hash_part_by_turn_colour = self.rand_64()
            self._hash_part_by_last_moved_piece = [self.rand_64() for _ in range(NumPieceNames)]

            unique_positions = Position.get_unique_positions(NumUniquePositions)
            self._hash_part_by_position = {
                i: {pos: self.rand_64() for pos in unique_positions}
                for i in range(NumPieceNames)
            }

            hash_part_by_turn_colour = self._hash_part_by_turn_colour
            hash_part_by_last_moved_piece = self._hash_part_by_last_moved_piece
            hash_part_by_position = self._hash_part_by_position
        else:
            self._hash_part_by_turn_colour = hash_part_by_turn_colour
            self._hash_part_by_last_moved_piece = hash_part_by_last_moved_piece
            self._hash_part_by_position = hash_part_by_position

    def toggle_piece(self, piece_name, position):
        self.value ^= self._hash_part_by_position[PieceNames[piece_name]][position]

    def toggle_last_moved_piece(self, piece_name):
        if piece_name != "INVALID":
            self.value ^= self._hash_part_by_last_moved_piece[piece_name]

    def toggle_turn(self):
        self.value ^= self._hash_part_by_turn_colour
