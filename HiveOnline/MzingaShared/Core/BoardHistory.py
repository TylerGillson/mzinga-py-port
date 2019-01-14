from MzingaShared.Core import Move
from MzingaShared.Core.Move import Move as MoveCls
from MzingaShared.Core.Piece import Piece


class BoardHistory:
    _items = []

    @property
    def count(self):
        return len(self._items)
    
    @property
    def last_move(self):
        if len(self._items) > 0:
            return self._items[-1]
        return None

    def __init__(self, board_history=None, board_history_string=None):
        if board_history:
            self._items = board_history.get_enumerator
        elif board_history_string:
            if board_history_string.isspace():
                raise ValueError("Invalid board_history_string.")

            split = board_history_string.split(';')
            for s in split:
                parse_item = BoardHistoryItem(s)
                self._items.append(parse_item)
        else:
            self._items = []

    def __repr__(self):
        items = [str(i) for i in self._items]
        if items:
            s = ""
            for i in items:
                s += i + ';'
            return s[:-1]
        return "No History"

    def add(self, move, original_position):
        item = BoardHistoryItem(move, original_position)
        self._items.append(item)

    def undo_last_move(self):
        if self.count > 0:
            item = self._items.pop()
            return item
        return None

    @property
    def get_enumerator(self):
        return self._items


class BoardHistoryItem:
    Move = None
    OriginalPosition = None

    def __init__(self, move=None, original_position=None, board_history_item_string=None):
        if board_history_item_string:
            if board_history_item_string.isspace():
                raise ValueError("Invalid board_history_item_string")

            split = list(filter(None, board_history_item_string.replace(' ', '>').split('>')))
            starting_piece = Piece(split[0])
            move = MoveCls(split[1])
            self.Move = move
            self.OriginalPosition = starting_piece.position
        else:
            if move is None:
                raise ValueError("Invalid move.")

            self.Move = move
            self.OriginalPosition = original_position

    def __repr__(self):
        starting_piece = Piece(self.Move.piece_name, self.OriginalPosition)
        return "%s > %s" % (starting_piece, self.Move)
