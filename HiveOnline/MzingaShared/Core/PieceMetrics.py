class PieceMetrics:
    InPlay = 0
    IsPinned = 0
    IsCovered = 0
    NoisyMoveCount = 0
    QuietMoveCount = 0
    FriendlyNeighborCount = 0
    EnemyNeighborCount = 0

    def reset(self):
        self.InPlay = 0
        self.IsPinned = 0
        self.IsCovered = 0
        self.NoisyMoveCount = 0
        self.QuietMoveCount = 0
        self.FriendlyNeighborCount = 0
        self.EnemyNeighborCount = 0
