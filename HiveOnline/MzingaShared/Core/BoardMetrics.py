from MzingaShared.Core import EnumUtils
from MzingaShared.Core.PieceMetrics import PieceMetrics


class BoardMetrics:
    PiecesInPlay = 0
    PiecesInHand = 0
    BoardState = None
    _piece_metrics = []

    def __init__(self):
        for i in range(EnumUtils.NumPieceNames):
            self._piece_metrics.append(PieceMetrics())

    def __getitem__(self, piece_name):
        return self._piece_metrics[EnumUtils.PieceNames[piece_name]]

    def reset(self):
        self.BoardState = "NotStarted"
        self.PiecesInHand = 0
        self.PiecesInPlay = 0

        pm_reset = PieceMetrics.reset
        list(map(pm_reset, self._piece_metrics))
