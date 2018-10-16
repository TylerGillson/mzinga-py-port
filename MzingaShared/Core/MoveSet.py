import sys
import os
from os.path import dirname
sys.path.append(dirname(dirname(os.getcwd())))  # Add root directory to PYTHONPATH

from MzingaShared.Core.Move import Move
from MzingaShared.Core.EnumUtils import PieceNames


class MoveSet:
    IsLocked = None
    _moves = []

    @property
    def count(self):
        return len(self._moves)

    def __init__(self, size=None, move_set_string=None, moves_list=None):
        if moves_list:
            self._moves = []
            for m in moves_list:
                self._moves.append(m)
            return

        if not move_set_string:
            self._moves = [Move()] * size if size else []
            self.IsLocked = False
            return

        if move_set_string.isspace():
            raise ValueError("Invalid move_set_string.")

        split = move_set_string.split(';')
        for s in split:
            parse_move = Move(move_string=s)
            self._moves.append(parse_move)

    def __getitem__(self, index):
        return self._moves[index]

    def __setitem__(self, key, value):
        self._moves[key] = value

    def __repr__(self):
        s = ""
        for move in self._moves:
            s += "%s%c" % (str(move), ';')
        return s[0:-1:]

    def add(self, value):
        if value is None:
            raise ValueError("Invalid move(s) provided.")
        if self.IsLocked:
            raise MoveSetIsLockedException

        if isinstance(value, Move):
            return self._moves.append(value)
        else:  # value is MoveSet or list of moves
            if value.count > 0:
                for move in value:
                    self._moves.append(move)

    def remove(self, value):
        if value is None:
            raise ValueError("Invalid move(s) provided.")
        if self.IsLocked:
            raise MoveSetIsLockedException

        if isinstance(value, Move):
            return self._moves.remove(value)
        else:  # value is MoveSet or list of moves
            for move in value:
                self._moves.remove(move)

    def contains(self, value):
        if value is None:
            raise ValueError("Invalid move or piece_name provided.")

        if isinstance(value, Move):
            return value in self._moves
        elif value in PieceNames.keys():  # value is a PieceName
            for move in self._moves:
                if move.piece_name == value:
                    return True
        return False

    def sort(self, sort_func, reverse):
        self._moves = sorted(self._moves, key=sort_func, reverse=reverse)

    def remove_range(self, start_idx):
        self._moves = self._moves[start_idx::]

    def lock(self):
        self.IsLocked = True


class MoveSetIsLockedException(Exception):
    def __init__(self):
        raise ValueError("This MoveSet is locked!")
