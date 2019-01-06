import math
from typing import List
from copy import deepcopy

BoardMetricWeights = {
    "QueenBeeLifeWeight": 0,
    "NonSlidingQueenBeeSpacesWeight": 1,
    "NoisyRingWeight": 2,
}
BoardMetricWeightsByInt = {v: k for k, v in BoardMetricWeights.items()}
NumBoardMetricWeights = 3


def read_metric_weights_xml(xml_elem):
    bmw = BoardMetricWeights()

    for elem in xml_elem:
        key = elem.tag
        value = float(elem.text)

        if key in BoardMetricWeights.keys():
            bmw.set(BoardMetricWeights[key], value)
    return bmw


class BoardMetricWeights(object):
    _board_metric_weights: List[float] = []

    @property
    def board_metric_weights(self):
        return self._board_metric_weights

    def __init__(self):
        self._board_metric_weights = [0] * NumBoardMetricWeights

    def get(self, idx):
        return self._board_metric_weights[idx]

    def set(self, idx, val):
        self._board_metric_weights[idx] = val

    def clone(self):
        return deepcopy(self)

    def get_normalized(self, target_max_value=100.0, is_round=True, decimals=6):
        if target_max_value <= 0.0:
            raise ValueError("Invalid target_max_value")

        clone = self.clone()

        # Copy board weights into local array
        dbl_weights: List[float] = clone._board_metric_weights

        max_weight = float("-inf")
        for weight in dbl_weights:
            max_weight = max(max_weight, abs(weight))

        # Normalize to new range
        for i in range(len(dbl_weights)):
            val = dbl_weights[i]
            dbl_weights[i] = math.copysign((abs(val) / max_weight) * target_max_value, val)

        # Populate clone with normalized weights
        for i in range(len(clone._board_metric_weights)):
            clone._board_metric_weights[i] = round(dbl_weights[i], decimals) if is_round else dbl_weights[i]

        return clone

    @staticmethod
    def iterate_over_weights(action):
        if action is None:
            raise ValueError("Invalid action.")

        for k in BoardMetricWeights.keys():
            action(k)

    @staticmethod
    def iterate_over_weights_result(action, results, **kwargs):
        if action is None:
            raise ValueError("Invalid action.")

        for k in BoardMetricWeights.keys():
            results.append(action(k, **kwargs))
        return results

