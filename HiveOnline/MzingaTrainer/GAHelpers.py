import random

from MzingaShared.Core.AI.BoardMetricWeights import BoardMetricWeights as BoardMetricWeightsCls
from MzingaShared.Core.AI.MetricWeights import MetricWeights as MetricWeightsCls

rand = random.Random()


def cross_over(weight_list_1, weight_list_2):
    if len(weight_list_1) != len(weight_list_2):
        raise ValueError("Weight lists must be the same length.")

    split_index = rand.randrange(0, len(weight_list_1))
    new_weights = weight_list_1[0:split_index] + weight_list_2[split_index:]

    if isinstance(weight_list_1, MetricWeightsCls):
        return MetricWeightsCls(game_type="Extended", weights=new_weights)
    else:
        return BoardMetricWeightsCls(weights=new_weights)


def mutate(weight_list):
    idx, sign = rand.randrange(0, len(weight_list)), rand.choice([1, -1])
    modulation_weight = random.choice([x for x in range(1, 11)])
    weight_list[idx] += (modulation_weight * sign)
    return weight_list


def generate_board_metric_weights(min_weight, max_weight):
    bmw = BoardMetricWeightsCls()

    def generate_weights(key):
        value = min_weight + (rand.random() * (max_weight - min_weight))
        bmw.set(key, value)

    bmw.iterate_over_weights(generate_weights)
    return bmw


def generate_metric_weights(min_weight, max_weight, game_type):
    mw = MetricWeightsCls(game_type)

    def generate_weights(bug_type, bug_type_weight):
        value = min_weight + (rand.random() * (max_weight - min_weight))
        mw.set(bug_type, bug_type_weight, value)

    mw.iterate_over_weights(generate_weights)
    return mw


def mix_metric_weights(mw_a, mw_b, min_mix, max_mix, game_type):
    mw = MetricWeightsCls(game_type)

    def mix_weights(bug_type, bug_type_weight):
        value = 0.5 * (mw_a.get(bug_type, bug_type_weight) + mw_b.get(bug_type, bug_type_weight))
        if value == 0.0:
            value = -0.01 + (rand.random() * 0.02)
        value = value * (min_mix + (rand.random() * abs(max_mix - min_mix)))
        mw.set(bug_type, bug_type_weight, value)

    mw.iterate_over_weights(mix_weights)
    return mw
