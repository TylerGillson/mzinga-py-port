from MzingaShared.Core.AI.BaseMetricWeights import BaseMetricWeights

board_metric_weights_dict = {
    "queen_bee_life_weight": 0,
    "queen_bee_tight_spaces_weight": 1,
    "noisy_ring_weight": 2,
}
board_metric_weights_dict_by_int = {v: k for k, v in board_metric_weights_dict.items()}
num_board_metric_weights = 3


def read_metric_weights_xml(xml_elem):
    bmw = BoardMetricWeights()

    for elem in xml_elem:
        key = elem.tag
        value = float(elem.text)

        if key in board_metric_weights_dict.keys():
            bmw.set(board_metric_weights_dict[key], value)
    return bmw


class BoardMetricWeights(BaseMetricWeights):
    __slots__ = "_board_metric_weights"

    @property
    def board_metric_weights(self):
        return self._board_metric_weights

    def __init__(self, weights=None):
        if weights:
            self._board_metric_weights = weights
        else:
            self._board_metric_weights = [0] * num_board_metric_weights

    def __len__(self):
        return len(self.board_metric_weights)

    def __getitem__(self, index):
        return self._board_metric_weights[index]

    def __setitem__(self, key, value):
        self._board_metric_weights[key] = value

    def get(self, metric_name):
        return self._board_metric_weights[board_metric_weights_dict[metric_name]]

    def set(self, idx, val):
        if not isinstance(idx, int):
            idx = board_metric_weights_dict[idx]
        self._board_metric_weights[idx] = val

    def clone(self):
        return super().clone(self)

    def get_normalized(self, target_max_value=100.0, is_round=True, decimals=6):
        return super().get_normalized(self, "_board_metric_weights", target_max_value, is_round, decimals)

    def add(self, a):
        self._board_metric_weights = super().add(self, a, "_board_metric_weights")

    def scale(self, factor):
        self._board_metric_weights = super().scale(self, factor, "_board_metric_weights")

    @staticmethod
    def iterate_over_weights(action):
        if action is None:
            raise ValueError("Invalid action.")

        _ = list(map(action, board_metric_weights_dict.keys()))

    @staticmethod
    def iterate_over_weights_result(action, results, **kwargs):
        if action is None:
            raise ValueError("Invalid action.")

        for k in board_metric_weights_dict.keys():
            results.append(action(k, **kwargs))
        return results
