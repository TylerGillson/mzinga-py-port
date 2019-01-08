from typing import List

from MzingaShared.Core import EnumUtils
from MzingaShared.Core.AI.BaseMetricWeights import BaseMetricWeights

BugTypeWeights = {
    "InPlayWeight": 0,
    "IsPinnedWeight": 1,
    "IsCoveredWeight": 2,
    "NoisyMoveWeight": 3,
    "QuietMoveWeight": 4,
    "FriendlyNeighborWeight": 5,
    "EnemyNeighborWeight": 6,
}
BugTypeWeightsByInt = {v: k for k, v in BugTypeWeights.items()}
NumBugTypeWeights = 7

# Define constructs for extended version:
ExtendedBugTypeWeights = {
    "CanMakeNoisyRingWeight": 7,
    "CanMakeDefenseRingWeight": 8,
}
ExtendedBugTypeWeightsByInt = {v: k for k, v in dict(BugTypeWeights, **ExtendedBugTypeWeights).items()}
ExtendedNumBugTypeWeights = 9


def read_metric_weights_xml(xml_elem, game_type):
    mw = MetricWeights(game_type)

    for elem in xml_elem:
        key = elem.tag
        value = float(elem.text)

        flag, bug_type, bug_type_weight = mw.try_parse_key_name(key)
        if flag:
            mw.set(bug_type, bug_type_weight, value + mw.get(bug_type, bug_type_weight))
    return mw


class MetricWeightsBase(object):

    def __init__(self, game_type):
        self.weight_max = NumBugTypeWeights if game_type == "Original" else ExtendedNumBugTypeWeights
        self.weight_dict = BugTypeWeights if game_type == "Original" else dict(BugTypeWeights, **ExtendedBugTypeWeights)
        self.weight_by_int_dict = BugTypeWeightsByInt if game_type == "Original" else ExtendedBugTypeWeightsByInt

    def iterate_over_weights(self, action):
        if action is None:
            raise ValueError("Invalid action.")

        for bug_type in EnumUtils.BugTypes.keys():
            bug_type_weight_int = 0
            while bug_type_weight_int < self.weight_max:
                bug_type_weight = self.weight_by_int_dict[bug_type_weight_int]
                action(bug_type, bug_type_weight)
                bug_type_weight_int += 1

    def iterate_over_weights_result(self, action, results, **kwargs):
        if action is None:
            raise ValueError("Invalid action.")

        for bug_type in EnumUtils.BugTypes.keys():
            bug_type_weight_int = 0
            while bug_type_weight_int < self.weight_max:
                bug_type_weight = self.weight_by_int_dict[bug_type_weight_int]
                results.append(action(bug_type, bug_type_weight, **kwargs))
                bug_type_weight_int += 1
        return results

    def get_key(self, bug_type, bug_type_weight):
        return EnumUtils.BugTypes[bug_type] * self.weight_max + self.weight_dict[bug_type_weight]

    def try_parse_key_name(self, key):
        if not key.isspace():
            try:
                split = key.split('.')
                bug_type = split[0]
                bug_type_weight = split[1]
                return True, bug_type, bug_type_weight
            except KeyError:
                pass

        bug_type = EnumUtils.BugTypes.values()[0]
        bug_type_weight = list(self.weight_dict.values())[0]
        return False, bug_type, bug_type_weight

    @staticmethod
    def get_key_name(bug_type, bug_type_weight):
        return "".join([bug_type, '.', bug_type_weight])


class MetricWeights(MetricWeightsBase):
    _bug_type_weights: List[float] = []

    @property
    def bug_type_weights(self):
        return self._bug_type_weights

    def __init__(self, game_type):
        super().__init__(game_type)
        self._bug_type_weights = [0] * EnumUtils.NumBugTypes * self.weight_max

    def get(self, bug_type, bug_type_weight):
        btw_key = self.get_key(bug_type, bug_type_weight)
        return self._bug_type_weights[btw_key]

    def set(self, bug_type, bug_type_weight, val):
        btw_key = self.get_key(bug_type, bug_type_weight)
        self._bug_type_weights[btw_key] = val

    def copy_from(self, source):
        if source is None:
            raise ValueError("Invalid source.")

        self._bug_type_weights = source.bug_type_weights

    def clone(self):
        return BaseMetricWeights.clone(self)

    def get_normalized(self, target_max_value=100.0, is_round=True, decimals=6):
        return BaseMetricWeights.get_normalized(self, "_bug_type_weights", target_max_value, is_round, decimals)

    def add(self, a):
        self._bug_type_weights = BaseMetricWeights.add(self._bug_type_weights, a, "_bug_type_weights")

    def scale(self, factor):
        self._bug_type_weights = BaseMetricWeights.scale(self, factor, "_bug_type_weights")
