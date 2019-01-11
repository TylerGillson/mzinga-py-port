import math
from typing import List
from copy import deepcopy


class BaseMetricWeights(object):

    @staticmethod
    def clone(obj):
        return deepcopy(obj)

    @staticmethod
    def get_normalized(obj, weights_list_name, target_max_value=100.0, is_round=True, decimals=6):
        if target_max_value <= 0.0:
            raise ValueError("Invalid target_max_value")

        # Copy bug weights into local array:
        clone = obj.clone()
        dbl_weights: List[float] = getattr(clone, weights_list_name)

        max_weight = float("-inf")
        for weight in dbl_weights:
            max_weight = max(max_weight, abs(weight))

        # Normalize to new range
        for i in range(len(dbl_weights)):
            val = dbl_weights[i]
            dbl_weights[i] = math.copysign((abs(val) / max_weight) * target_max_value, val)

        # Populate clone with normalized weights
        if is_round:
            dbl_weights = list(map(lambda x: round(x, decimals), dbl_weights))

        setattr(clone, weights_list_name, dbl_weights)
        return clone

    @staticmethod
    def add(obj, a, weights_list_name):
        obj_weights = getattr(obj, weights_list_name)
        a_weights = getattr(a, weights_list_name)

        if obj_weights is None or a_weights is None:
            raise ValueError("Invalid metric_weights property name.")

        return [sum(x) for x in zip(obj_weights, a_weights)]

    @staticmethod
    def scale(obj, factor, weights_list_name):
        obj_weights = getattr(obj, weights_list_name)

        if obj_weights is None:
            raise ValueError("Invalid metric_weights property name.")

        return list(map(lambda x: x * factor, obj_weights))
