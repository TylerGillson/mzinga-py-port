from MzingaShared.Core import EnumUtils
from MzingaShared.Core.PieceMetrics import PieceMetrics, ExtendedPieceMetrics


class BoardMetrics:
    # Original Board Metrics:
    PiecesInPlay = 0
    PiecesInHand = 0

    # Extended Board Metrics:
    BlackQueenLife = 0
    WhiteQueenLife = 0
    BlackNonSlidingQueenSpaces = 0
    WhiteNonSlidingQueenSpaces = 0
    BlackNoisyRing = 0  # Is there a ring which Black would consider Noisy? (Contains BQ, or Black-heavy piece ratio)
    WhiteNoisyRing = 0  # Is there a ring which White would consider Noisy? (Contains WQ, or White-heavy piece ratio)

    BoardState = None
    GameType = None
    _piece_metrics = []

    def __init__(self, game_type):
        self.GameType = game_type

        for i in range(EnumUtils.NumPieceNames):
            self._piece_metrics.append(PieceMetrics() if game_type == "Original" else ExtendedPieceMetrics())

    def __getitem__(self, piece_name):
        return self._piece_metrics[EnumUtils.PieceNames[piece_name]]

    def reset(self):
        self.BoardState = "NotStarted"
        self.PiecesInHand = 0
        self.PiecesInPlay = 0
        self.BlackQueenLife = 0
        self.WhiteQueenLife = 0
        self.BlackNonSlidingQueenSpaces = 0
        self.WhiteNonSlidingQueenSpaces = 0
        self.BlackNoisyRing = 0
        self.WhiteNoisyRing = 0

        pm_reset = PieceMetrics.reset if self.GameType == "Original" else ExtendedPieceMetrics.reset
        list(map(pm_reset, self._piece_metrics))
