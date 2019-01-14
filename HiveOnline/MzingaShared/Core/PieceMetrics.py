class PieceMetrics(object):
    __slots__ = "in_play", "is_pinned", "is_covered", \
                "noisy_move_count", "quiet_move_count", \
                "friendly_neighbour_count", "enemy_neighbour_count"

    def __init__(self):
        self.in_play = 0
        self.is_pinned = 0
        self.is_covered = 0
        self.noisy_move_count = 0
        self.quiet_move_count = 0
        self.friendly_neighbour_count = 0
        self.enemy_neighbour_count = 0

    def reset(self):
        self.in_play = 0
        self.is_pinned = 0
        self.is_covered = 0
        self.noisy_move_count = 0
        self.quiet_move_count = 0
        self.friendly_neighbour_count = 0
        self.enemy_neighbour_count = 0


class ExtendedPieceMetrics(PieceMetrics):
    __slots__ = "can_make_noisy_ring", "can_make_defense_ring"

    def __init__(self):
        super().__init__()
        self.can_make_noisy_ring = 0
        self.can_make_defense_ring = 0

    def reset(self):
        super().reset()
        self.can_make_noisy_ring = 0
        self.can_make_defense_ring = 0
