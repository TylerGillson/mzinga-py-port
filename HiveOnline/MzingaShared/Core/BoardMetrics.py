from MzingaShared.Core import EnumUtils
from MzingaShared.Core.PieceMetrics import PieceMetrics, ExtendedPieceMetrics


class BoardMetrics(object):
    __slots__ = "game_type", "board_state", "pieces_in_play", "pieces_in_hand", \
                "black_queen_life", "white_queen_life", "black_queen_tight_spaces", "white_queen_tight_spaces", \
                "black_noisy_ring", "white_noisy_ring", "_piece_metrics"

    def __init__(self, game_type):
        self.game_type = game_type
        self.board_state = None
        self.pieces_in_play = 0
        self.pieces_in_hand = 0
        self._piece_metrics = [PieceMetrics() if game_type == "Original" else ExtendedPieceMetrics()
                               for _ in range(EnumUtils.num_piece_names)]

        # Extended Board Metrics:
        if game_type == "Extended":
            self.black_queen_life = 0
            self.white_queen_life = 0
            self.black_queen_tight_spaces = 0
            self.white_queen_tight_spaces = 0
            self.black_noisy_ring = 0  # (Ring that contains BQ, or has Black-heavy piece ratio)
            self.white_noisy_ring = 0  # (Ring that contains WQ, or has White-heavy piece ratio)

    def __getitem__(self, piece_name):
        return self._piece_metrics[EnumUtils.piece_names[piece_name]]

    def reset(self):
        self.board_state = "NotStarted"
        self.pieces_in_hand = 0
        self.pieces_in_play = 0

        if self.game_type == "Extended":
            self.black_queen_life = 0
            self.white_queen_life = 0
            self.black_queen_tight_spaces = 0
            self.white_queen_tight_spaces = 0
            self.black_noisy_ring = 0
            self.white_noisy_ring = 0

        pm_reset = PieceMetrics.reset if self.game_type == "Original" else ExtendedPieceMetrics.reset
        list(map(pm_reset, self._piece_metrics))
