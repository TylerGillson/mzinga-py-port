import sys
import os
from os.path import dirname
sys.path.append(dirname(dirname(dirname(os.getcwd()))))  # Add root directory to PYTHONPATH

import math
from copy import deepcopy
from MzingaShared.Core import EnumUtils

BugTypeWeights = {
    "InPlayWeight": 0,
    "IsPinnedWeight": 0,
    "IsCoveredWeight": 0,
    "NoisyMoveWeight": 0,
    "QuietMoveWeight": 0,
    "FriendlyNeighborWeight": 0,
    "EnemyNeighborWeight": 0,
}
BugTypeWeightsByInt = {v: k for k, v in BugTypeWeights.items()}


class MetricWeights:
    NumBugTypeWeights = 7
    KeySeparator = "."
    _bug_type_weights = []

    @property
    def bug_type_weights(self):
        return self._bug_type_weights

    def __init__(self):
        self._bug_type_weights = [0] * EnumUtils.NumBugTypes * self.NumBugTypeWeights

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
        return deepcopy(self)

    def get_normalized(self, target_max_value=100.0, is_round=True, decimals=6):
        if target_max_value <= 0.0:
            raise ValueError("Invalid target_max_value")

        clone = self.clone()

        # Copy bug weights into local array
        dbl_weights = deepcopy(clone._bug_type_weights)

        max_weight = float("-inf")
        for weight in dbl_weights:
            max_weight = max(max_weight, abs(weight))

        # Normalize to new range
        for i in range(len(dbl_weights)):
            val = dbl_weights[i]
            dbl_weights[i] = math.copysign((abs(val) / max_weight) * target_max_value, val)

        # Populate clone with normalized weights
        for i in range(len(clone._bug_type_weights)):
            clone._bug_type_weights[i] = round(dbl_weights[i], decimals) if is_round else dbl_weights[i]

        return clone

    def add(self, a):
        if a is None:
            raise ValueError("a")

        for i in range(len(self._bug_type_weights)):
            self._bug_type_weights[i] += a.bug_type_weights[i]

    def scale(self, factor):
        for i in range(len(self._bug_type_weights)):
            self._bug_type_weights[i] *= factor

    def read_metric_weights_xml(self, xml_tree):
        mw = MetricWeights()
        root = xml_tree.getroot()

        for elem in root:
            if elem == root and not elem.text == "MetricWeights":
                key = elem.attrib
                value = elem.text

                flag, bug_type, bug_type_weight = self.try_parse_key_name(key)
                if flag:
                    mw.set(bug_type, bug_type_weight, value + mw.get(bug_type, bug_type_weight))
        return mw

    def try_parse_key_name(self, key):
        if not key.isspace():
            try:
                split = key.Split(self.KeySeparator)

                bug_type_weight = split[-1]
                bug_type = split[-2]
                return True, bug_type, bug_type_weight
            except KeyError:
                pass

        global BugTypeWeights
        bug_type = EnumUtils.BugTypes.values()[0]
        bug_type_weight = BugTypeWeights.values()[0]
        return False, bug_type, bug_type_weight

    def get_key_name(self, bug_type, bug_type_weight):
        return "".join([self.KeySeparator, bug_type, bug_type_weight])

    def iterate_over_weights(self, action):
        if action is None:
            raise ValueError("Invalid action.")

        for bug_type in EnumUtils.BugTypes.values():
            bug_type_weight_int = 0
            while bug_type_weight_int < self.NumBugTypeWeights:
                bug_type_weight = BugTypeWeightsByInt[bug_type_weight_int]
                action(bug_type, bug_type_weight)
                bug_type_weight_int += 1

    def get_key(self, bug_type, bug_type_weight):
        return BugTypeWeights[bug_type] * self.NumBugTypeWeights + bug_type_weight
