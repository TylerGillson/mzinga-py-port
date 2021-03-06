﻿from Utils.BinarySearch import binary_search_ext


class EvaluatedMoveCollection(object):
    __slots__ = "_evaluated_moves"

    @property
    def count(self):
        return len(self._evaluated_moves)

    @property
    def best_move(self):
        if len(self._evaluated_moves) > 0:
            return self._evaluated_moves[0]
        return None

    def __init__(self, evaluated_moves=None, re_sort=None):
        if evaluated_moves:
            self.add(evaluated_moves, re_sort)
        else:
            self._evaluated_moves = []

    def __getitem__(self, index):
        return self._evaluated_moves[index]

    def __repr__(self):
        ems = [em for em in self._evaluated_moves]
        ems_strs = list(map(lambda x: "%s%c" % (x.move, ';'), ems))
        return "".join(ems_strs)[0:-1:]

    def add(self, evaluated_moves=None, re_sort=None, evaluated_move=None):
        if evaluated_move:
            index = self.search_for(evaluated_move)
            if index == len(self._evaluated_moves):
                self._evaluated_moves.append(evaluated_move)
            else:
                self._evaluated_moves.insert(index, evaluated_move)
        else:
            for move in evaluated_moves:
                if re_sort:
                    self.add(evaluated_move=move)
                else:
                    self._evaluated_moves.append(move)

    def prune_game_losing_moves(self):
        first_losing_move_idx = -1

        for i in range(len(self._evaluated_moves)):
            if self._evaluated_moves[i].score_after_move == float("-inf"):
                first_losing_move_idx = i
                break

        if first_losing_move_idx > 0:
            self._evaluated_moves = self._evaluated_moves[0:first_losing_move_idx:]

    def get_enumerator(self):
        return self._evaluated_moves

    def search_for(self, evaluated_move):
        return binary_search_ext(self._evaluated_moves, 0, len(self._evaluated_moves)-1, evaluated_move)
