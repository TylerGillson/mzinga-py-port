class PieceMetrics:
    __slots__ = "InPlay", "IsPinned", "IsCovered", \
                "NoisyMoveCount", "QuietMoveCount", \
                "FriendlyNeighbourCount", "EnemyNeighbourCount"

    def __init__(self):
        self.InPlay = 0
        self.IsPinned = 0
        self.IsCovered = 0
        self.NoisyMoveCount = 0
        self.QuietMoveCount = 0
        self.FriendlyNeighbourCount = 0
        self.EnemyNeighbourCount = 0

    def reset(self):
        self.InPlay = 0
        self.IsPinned = 0
        self.IsCovered = 0
        self.NoisyMoveCount = 0
        self.QuietMoveCount = 0
        self.FriendlyNeighbourCount = 0
        self.EnemyNeighbourCount = 0


class ExtendedPieceMetrics(PieceMetrics):
    __slots__ = "CanMakeNoisyRing", "CanMakeDefenseRing"

    def __init__(self):
        super().__init__()
        self.CanMakeNoisyRing = 0
        self.CanMakeDefenseRing = 0

    def reset(self):
        super().reset()
        self.CanMakeNoisyRing = 0
        self.CanMakeDefenseRing = 0
