from typing import List

from MzingaShared.Core.AI.BaseMetricWeights import BaseMetricWeights

BoardMetricWeightsDict = {
    "QueenBeeLifeWeight": 0,
    "NonSlidingQueenBeeSpacesWeight": 1,
    "NoisyRingWeight": 2,
}
BoardMetricWeightsDictByInt = {v: k for k, v in BoardMetricWeightsDict.items()}
NumBoardMetricWeights = 3


def read_metric_weights_xml(xml_elem):
    bmw = BoardMetricWeights()

    for elem in xml_elem:
        key = elem.tag
        value = float(elem.text)

        if key in BoardMetricWeightsDict.keys():
            bmw.set(BoardMetricWeightsDict[key], value)
    return bmw


class BoardMetricWeights(BaseMetricWeights):
    _board_metric_weights: List[float] = []

    @property
    def board_metric_weights(self):
        return self._board_metric_weights

    def __init__(self):
        self._board_metric_weights = [0] * NumBoardMetricWeights

    def get(self, metric_name):
        return self._board_metric_weights[BoardMetricWeightsDict[metric_name]]

    def set(self, idx, val):
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

        _ = list(map(action, BoardMetricWeightsDict.keys()))

    @staticmethod
    def iterate_over_weights_result(action, results, **kwargs):
        if action is None:
            raise ValueError("Invalid action.")

        for k in BoardMetricWeightsDict.keys():
            results.append(action(k, **kwargs))
        return results

