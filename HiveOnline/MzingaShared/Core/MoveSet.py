from MzingaShared.Core.Move import Move
from MzingaShared.Core.EnumUtils import PieceNames


class MoveSet(object):
    __slots__ = "_moves", "is_locked"

    @property
    def count(self):
        return len(self._moves)

    def __init__(self, size=None, move_set_string=None, moves_list=None):
        self.is_locked = None
        self._moves = []

        if moves_list:
            self._moves = [m for m in moves_list]
            return

        if not move_set_string:
            self._moves = [Move()] * size if size else []
            self.is_locked = False
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
        s = "".join(["%s%c" % (str(m), ';') for m in self._moves])
        return s[0:-1:]

    def add(self, value):
        if value is None:
            raise ValueError("Invalid move(s) provided.")
        if self.is_locked:
            raise MoveSetIsLockedException

        if isinstance(value, Move):
            return self._moves.append(value)
        else:
            ext_iter = value._moves if isinstance(value, MoveSet) else value
            self._moves.extend(ext_iter)

    def remove(self, value):
        if value is None:
            raise ValueError("Invalid move(s) provided.")
        if self.is_locked:
            raise MoveSetIsLockedException

        if isinstance(value, Move) and value in self._moves:
            return self._moves.remove(value)
        else:
            diff_iter = value._moves if isinstance(value, MoveSet) else value
            self._moves = list(set(self._moves) - set(diff_iter))

    def contains(self, value):
        if value is None:
            raise ValueError("Invalid move or piece_name provided.")

        if isinstance(value, Move):
            return value in self._moves
        elif value in PieceNames.keys():  # value is a PieceName
            if value in [m.piece_name for m in self._moves]:
                return True
        return False

    def sort(self, sort_func, reverse):
        self._moves = sorted(self._moves, key=sort_func, reverse=reverse)

    def remove_range(self, start_idx):
        self._moves = self._moves[start_idx::]

    def lock(self):
        self.is_locked = True


class MoveSetIsLockedException(Exception):
    def __init__(self):
        raise ValueError("This MoveSet is locked!")
