class PieceMetrics(object):
    __slots__ = "in_play", "is_pinned", "is_covered", \
                "noisy_move_count", "quiet_move_count", \
                "friendly_neighbour_count", "enemy_neighbour_count"

    def __init__(self, metric_string=None):
        if metric_string is None:
            self.in_play = 0
            self.is_pinned = 0
            self.is_covered = 0
            self.noisy_move_count = 0
            self.quiet_move_count = 0
            self.friendly_neighbour_count = 0
            self.enemy_neighbour_count = 0
        else:
            values = metric_string.split(';')
            self.in_play, self.is_pinned, self.is_covered, \
                self.noisy_move_count, self.quiet_move_count, \
                self.friendly_neighbour_count, self.enemy_neighbour_count = list(map(int, values))

    def __repr__(self):
        attrs = list(map(str, [self.in_play, self.is_pinned, self.is_covered,
                               self.noisy_move_count, self.quiet_move_count,
                               self.friendly_neighbour_count, self.enemy_neighbour_count]))
        return "".join(["".join([x, ';']) for x in attrs])[0:-1]

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

    def __init__(self, metric_string=None):
        if metric_string is None:
            super().__init__()
            self.can_make_noisy_ring = 0
            self.can_make_defense_ring = 0
        else:
            super().__init__(metric_string=metric_string[0:-4])
            self.can_make_noisy_ring, self.can_make_defense_ring = int(metric_string[-3]), int(metric_string[-1])

    def __repr__(self):
        s = super().__repr__()
        return "".join([s, ';', str(self.can_make_noisy_ring), ';', str(self.can_make_defense_ring)])

    def reset(self):
        super().reset()
        self.can_make_noisy_ring = 0
        self.can_make_defense_ring = 0
