import sys
import os
from os.path import dirname
sys.path.append(dirname(dirname(os.getcwd())))  # Add root directory to PYTHONPATH

from MzingaShared.Core import EnumUtils
from MzingaShared.Core.PieceMetrics import PieceMetrics


class BoardMetrics:
    PiecesInPlay = 0
    PiecesInHand = 0
    BoardState = None
    _piece_metrics = [0] * EnumUtils.NumPieceNames

    def __init__(self):
        for i in range(EnumUtils.NumPieceNames):
            self._piece_metrics[i] = PieceMetrics()

    def __getitem__(self, piece_name):
        return self._piece_metrics[EnumUtils.PieceNames[piece_name]]

    def reset(self):
        self.BoardState = "NotStarted"
        self.PiecesInHand = 0
        self.PiecesInPlay = 0

        for pm in self._piece_metrics:
            pm.reset()
