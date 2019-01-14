from MzingaShared.Core import EnumUtils
from MzingaShared.Core.AI.BaseMetricWeights import BaseMetricWeights

bug_type_weights = {
    "in_play_weight": 0,
    "is_pinned_weight": 1,
    "is_covered_weight": 2,
    "noisy_move_weight": 3,
    "quiet_move_weight": 4,
    "friendly_neighbour_weight": 5,
    "enemy_neighbour_weight": 6,
}
bug_type_weights_by_int = {v: k for k, v in bug_type_weights.items()}
num_bug_type_weights = 7

# Define constructs for extended version:
extended_bug_type_weights = {
    "can_make_noisy_ring_weight": 7,
    "can_make_defense_ring_weight": 8,
}
extended_bug_type_weights_by_int = {v: k for k, v in dict(bug_type_weights, **extended_bug_type_weights).items()}
extended_num_bug_type_weights = 9


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
    __slots__ = "weight_max", "weight_dict", "weight_by_int_dict"

    def __init__(self, game_type):
        self.weight_max = num_bug_type_weights if game_type == "Original" else extended_num_bug_type_weights
        self.weight_dict = \
            bug_type_weights if game_type == "Original" else dict(bug_type_weights, **extended_bug_type_weights)
        self.weight_by_int_dict = \
            bug_type_weights_by_int if game_type == "Original" else extended_bug_type_weights_by_int

    def iterate_over_weights(self, action):
        if action is None:
            raise ValueError("Invalid action.")

        for bug_type in EnumUtils.bug_types.keys():
            bug_type_weight_int = 0
            while bug_type_weight_int < self.weight_max:
                bug_type_weight = self.weight_by_int_dict[bug_type_weight_int]
                action(bug_type, bug_type_weight)
                bug_type_weight_int += 1

    def iterate_over_weights_result(self, action, results, **kwargs):
        if action is None:
            raise ValueError("Invalid action.")

        for bug_type in EnumUtils.bug_types.keys():
            bug_type_weight_int = 0
            while bug_type_weight_int < self.weight_max:
                bug_type_weight = self.weight_by_int_dict[bug_type_weight_int]
                results.append(action(bug_type, bug_type_weight, **kwargs))
                bug_type_weight_int += 1
        return results

    def get_key(self, bug_type, bug_type_weight):
        return EnumUtils.bug_types[bug_type] * self.weight_max + self.weight_dict[bug_type_weight]

    def try_parse_key_name(self, key):
        if not key.isspace():
            try:
                split = key.split('.')
                bug_type = split[0]
                bug_type_weight = split[1]
                return True, bug_type, bug_type_weight
            except KeyError:
                pass

        bug_type = EnumUtils.bug_types.values()[0]
        bug_type_weight = list(self.weight_dict.values())[0]
        return False, bug_type, bug_type_weight

    @staticmethod
    def get_key_name(bug_type, bug_type_weight):
        return "".join([bug_type, '.', bug_type_weight])


class MetricWeights(MetricWeightsBase):
    __slots__ = "_bug_type_weights"

    @property
    def bug_type_weights(self):
        return self._bug_type_weights

    def __init__(self, game_type, weights=None):
        super().__init__(game_type)

        if weights:
            self._bug_type_weights = weights
        else:
            self._bug_type_weights = [0] * EnumUtils.num_bug_types * self.weight_max

    def __len__(self):
        return len(self._bug_type_weights)

    def __getitem__(self, index):
        return self._bug_type_weights[index]

    def __setitem__(self, key, value):
        self._bug_type_weights[key] = value

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
