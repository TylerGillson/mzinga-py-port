UnevaluatedMoveScore = float("-inf")


class EvaluatedMove:
    move = None
    score_after_move = None
    depth = None

    def __init__(self, move, score_after_move=UnevaluatedMoveScore, depth=0):
        self.move = move
        self.score_after_move = score_after_move
        self.depth = depth

    def __eq__(self, other):
        if other is None:
            return False
        return self.depth == other.depth and self.score_after_move == other.score_after_move and self.move == other.move

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.get_hash_code()

    def __repr__(self):
        return "%s%c%d%c%d" % (self.move, ';', self.depth, ';', self.score_after_move)

    def compare_to(self, evaluated_move):
        return evaluated_move.score_after_move.compare_to(self.score_after_move)

    @staticmethod
    def equals(a, b):
        if not a:
            return b
        return a == b

    def get_hash_code(self):
        hash_code = 17
        hash_code = hash_code * 31 + self.move.get_hash_code()
        hash_code = hash_code * 31 + hash(self.score_after_move)
        hash_code = hash_code * 31 + self.depth
        return hash_code
