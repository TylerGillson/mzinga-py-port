from MzingaShared.Core import EnumUtils
from MzingaShared.Core.PieceMetrics import PieceMetrics, ExtendedPieceMetrics


class BoardMetrics(object):
    __slots__ = "game_type", "board_state", "pieces_in_play", "pieces_in_hand", \
                "black_queen_life", "white_queen_life", "black_queen_tight_spaces", "white_queen_tight_spaces", \
                "black_noisy_ring", "white_noisy_ring", "_piece_metrics"

    def __init__(self, game_type, metric_string=None):
        if metric_string is None:
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
        else:
            pm_start = metric_string.find('[')
            base_values = metric_string[0:pm_start-1].split(';')
            self.game_type = base_values[0]
            self.board_state = base_values[1]
            self.pieces_in_play = int(base_values[2])
            self.pieces_in_hand = int(base_values[3])

            if self.game_type == "Extended":
                self.black_queen_life, self.white_queen_life, \
                    self.black_noisy_ring, self.white_noisy_ring, \
                    self.black_queen_tight_spaces, self.white_queen_tight_spaces = list(map(int, base_values[4:10]))

            piece_metrics_str = metric_string[pm_start+1:-1]
            piece_metric_strs = piece_metrics_str.replace(',', '').split(' ')
            self._piece_metrics = [PieceMetrics(metric_string=piece_metric_strs[i]) if game_type == "Original" else
                                   ExtendedPieceMetrics(metric_string=piece_metric_strs[i])
                                   for i in range(EnumUtils.num_piece_names)]

    def __repr__(self):
        base = [self.game_type, self.board_state, str(self.pieces_in_play), str(self.pieces_in_hand)]
        if self.game_type == "Extended":
            base.extend([str(self.black_queen_life), str(self.white_queen_life),
                         str(self.black_noisy_ring), str(self.white_noisy_ring),
                         str(self.black_queen_tight_spaces), str(self.white_queen_tight_spaces)])

        s = "".join(["".join([x, ';']) for x in base])
        return "".join([s, str(self._piece_metrics)])

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
