﻿import sys
import os
from os.path import dirname
sys.path.append(dirname(os.getcwd()))  # Add root directory to PYTHONPATH

import datetime
import random
import uuid
import xml.etree.ElementTree as ElementTree

from MzingaShared.Core.AI.MetricWeights import MetricWeights
from MzingaTrainer.EloUtils import EloUtils


class Profile:
    Id = None
    _name = None
    _random = None

    Generation = 0
    ParentA = None
    ParentB = None

    StartMetricWeights = None
    EndMetricWeights = None
    CreationTimestamp = None
    LastUpdatedTimestamp = None

    Wins = 0
    Losses = 0
    Draws = 0
    EloRating = EloUtils.DefaultRating

    @property
    def name(self):
        return self._name if not (self._name is None or self._name.isspace()) else str(self.Id)[0:8:]

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def total_games(self):
        return self.Wins + self.Losses + self.Draws

    @property
    def random(self):
        if self._random:
            return self._random
        self._random = random.random

    def __init__(self, i_id, name, start_metric_weights, end_metric_weights, **kwargs):
        if "generation" in kwargs and kwargs.get("generation") < 0:
            raise ValueError("Invalid generation.")

        if "parent_a" in kwargs and kwargs.get("parent_a") is None:
            raise ValueError("Invalid parent_a.")

        if "parent_b" in kwargs and kwargs.get("parent_b") is None:
            raise ValueError("Invalid parent_b.")

        if "elo_rating" in kwargs and kwargs.get("elo_rating") < EloUtils.MinRating:
            raise ValueError("Invalid elo_rating.")

        if "start_metric_weights" in kwargs and kwargs.get("start_metric_weights") is None:
            raise ValueError("Invalid start_metric_weights.")

        if "end_metric_weights" in kwargs and kwargs.get("end_metric_weights") is None:
            raise ValueError("Invalid end_metric_weights.")

        if "wins" in kwargs and kwargs.get("wins") < 0:
            raise ValueError("Invalid wins.")

        if "losses" in kwargs and kwargs.get("losses") < 0:
            raise ValueError("Invalid losses.")

        if "draws" in kwargs and kwargs.get("draws") < 0:
            raise ValueError("Invalid draws.")

        self.Id = i_id
        self.Name = name
        self.StartMetricWeights = start_metric_weights
        self.EndMetricWeights = end_metric_weights
        self.CreationTimestamp = kwargs.pop("creation_timestamp") \
            if "creation_timestamp" in kwargs else datetime.datetime.now()
        self.LastUpdatedTimestamp = kwargs.pop("last_updated_timestamp") \
            if "last_updated_timestamp" in kwargs else datetime.datetime.now()

        self.Generation = kwargs.pop("generation") if "generation" in kwargs else 0

        if "parent_a" in kwargs:
            self.ParentA = kwargs.pop("parent_a")
        if "parent_b" in kwargs:
            self.ParentB = kwargs.pop("parent_b")
        if "elo_rating" in kwargs:
            self.EloRating = kwargs.pop("elo_rating")
        if "wins" in kwargs:
            self.Wins = kwargs.pop("wins")
        if "losses" in kwargs:
            self.Losses = kwargs.pop("losses")
        if "draws" in kwargs:
            self.Draws = kwargs.pop("draws")

    def update_record(self, rating, result):
        if rating < EloUtils.MinRating:
            raise ValueError("Invalid rating.")

        self.EloRating = rating

        if result == "Loss":
            self.Losses += 1
        elif result == "Draw":
            self.Draws += 1
        else:  # Win
            self.Wins += 1

        self.update()

    def update_metric_weights(self, start_metric_weights, end_metric_weights):
        if start_metric_weights is None:
            raise ValueError("Invalid start_metric_weights.")
        if end_metric_weights is None:
            raise ValueError("Invalid end_metric_weights.")

        self.StartMetricWeights = start_metric_weights
        self.EndMetricWeights = end_metric_weights

        self.update()

    def update(self):
        self.LastUpdatedTimestamp = datetime.datetime.now()

    def write_xml(self, output_stream):
        if output_stream is None:
            raise ValueError("Invalid output_stream.")

        root = ElementTree.Element("Profile")
        _ = ElementTree.SubElement(root, "Id").text = str(self.Id)

        if not (self._name is None or self._name.isspace()):
            _ = ElementTree.SubElement(root, "Name").text = self._name.strip()
        if self.ParentA is not None:
            _ = ElementTree.SubElement(root, "ParentA").text = self.ParentA
        if self.ParentB is not None:
            _ = ElementTree.SubElement(root, "ParentB").text = self.ParentB

        _ = ElementTree.SubElement(root, "EloRating").text = self.EloRating
        _ = ElementTree.SubElement(root, "Wins").text = self.Wins
        _ = ElementTree.SubElement(root, "Losses").text = self.Losses
        _ = ElementTree.SubElement(root, "Draws").text = self.Draws
        _ = ElementTree.SubElement(root, "Creation").text = self.CreationTimestamp
        _ = ElementTree.SubElement(root, "LastUpdated").text = self.LastUpdatedTimestamp

        start_metric_weights = ElementTree.SubElement(root, "StartMetricWeights")
        end_metric_weights = ElementTree.SubElement(root, "EndMetricWeights")
        parent_node = start_metric_weights

        def write_weights(bug_type, bug_type_weight):
            key = MetricWeights().get_key_name(bug_type, bug_type_weight)
            w_value = self.StartMetricWeights.get(bug_type, bug_type_weight)
            _ = ElementTree.SubElement(parent_node, key).text = w_value

        MetricWeights().iterate_over_weights(write_weights)
        parent_node = end_metric_weights
        MetricWeights().iterate_over_weights(write_weights)

        tree = ElementTree.ElementTree(root)
        tree.write(output_stream)

    @staticmethod
    def read_xml(input_stream):
        if input_stream is None:
            raise ValueError("Invalid input_stream.")

        r_id = None
        r_name = None
        generation = 0
        parent_a = None
        parent_b = None
        elo_rating = EloUtils.DefaultRating
        wins = 0
        losses = 0
        draws = 0
        start_metric_weights = None
        end_metric_weights = None
        creation_timestamp = datetime.datetime.now()
        last_updated_timestamp = creation_timestamp

        reader = ElementTree.parse(input_stream)
        root = reader.getroot()

        for node in root:
            if node.attrib == "Id":
                r_id = uuid.UUID(uuid.UUID(node.text).hex)
            if node.attrib == "Name":
                r_name = node.text
            if node.attrib == "Generation":
                generation = int(node.text)
            if node.attrib == "ParentA":
                parent_a = uuid.UUID(uuid.UUID(node.text).hex)
            if node.attrib == "ParentB":
                parent_a = uuid.UUID(uuid.UUID(node.text).hex)
            if node.attrib == "EloRating":
                elo_rating = int(node.text)
            if node.attrib == "Wins":
                wins = int(node.text)
            if node.attrib == "Losses":
                losses = int(node.text)
            if node.attrib == "Draws":
                draws = int(node.text)
            if node.attrib == "Creation":
                creation_timestamp = datetime.datetime.strptime(node.text, "YYYY-MM-DD %H:%M%:%S")
            if node.attrib == "LastUpdated":
                last_updated_timestamp = datetime.datetime.strptime(node.text, "YYYY-MM-DD %H:%M%:%S")
            if node.attrib in ["MetricWeights", "StartMetricWeights"]:
                start_metric_weights = MetricWeights().read_metric_weights_xml([subelem for subelem in node])
            if node.attrib == "EndMetricWeights":
                end_metric_weights = MetricWeights().read_metric_weights_xml([subelem for subelem in node])

        if r_name is None:
            r_name = generate_name(r_id)
        if end_metric_weights is None:
            end_metric_weights = start_metric_weights

        kwargs = dict([parent_a, parent_b, elo_rating, wins, losses, draws,
                       start_metric_weights, end_metric_weights, creation_timestamp, last_updated_timestamp])
        return Profile(r_id, r_name, generation, **kwargs)

    @staticmethod
    def generate(min_weight, max_weight):
        start_metric_weights = generate_metric_weights(min_weight, max_weight)
        end_metric_weights = generate_metric_weights(min_weight, max_weight)

        g_id = uuid.uuid4()
        g_name = generate_name(g_id)

        return Profile(g_id, g_name, start_metric_weights, end_metric_weights)

    @staticmethod
    def mate(parent_a, parent_b, min_mix, max_mix):
        if parent_a is None:
            raise ValueError("Invalid parent_a.")
        if parent_b is None:
            raise ValueError("Invalid parent_b.")
        if min_mix > max_mix:
            raise ValueError("Invalid min/max_mixes.")

        m_id = uuid.uuid4()
        name = generate_name(m_id)
        elo_rating = EloUtils.DefaultRating
        generation = max(parent_a.Generation, parent_b.Generation) + 1

        start_metric_weights = mix_metric_weights(
            parent_a.StartMetricWeights.get_normalized(),
            parent_b.StartMetricWeights.get_normalized(),
            min_mix, max_mix)

        end_metric_weights = mix_metric_weights(
            parent_a.EndMetricWeights.get_normalized(),
            parent_b.EndMetricWeights.get_normalized(),
            min_mix, max_mix)

        creation_timestamp = datetime.datetime.now()

        kwargs = dict([generation, parent_a.Id, parent_b.Id, elo_rating, creation_timestamp])
        return Profile(m_id, name, start_metric_weights, end_metric_weights, **kwargs)


def generate_metric_weights(min_weight, max_weight):
    mw = MetricWeights()

    def generate_weights(bug_type, bug_type_weight):
        value = min_weight + (random.random() * (max_weight - min_weight))
        mw.set(bug_type, bug_type_weight, value)

    mw.iterate_over_weights(generate_weights)
    return mw


def mix_metric_weights(mw_a, mw_b, min_mix, max_mix):
    mw = MetricWeights()

    def mix_weights(bug_type, bug_type_weight):
        value = 0.5 * (mw_a.get(bug_type, bug_type_weight) + mw_b.get(bug_type, bug_type_weight))
        if value == 0.0:
            value = -0.01 + (random.random() * 0.02)
        value = value * (min_mix + (random.random() * abs(max_mix - min_mix)))
        mw.set(bug_type, bug_type_weight, value)

    mw.iterate_over_weights(mix_weights)
    return mw


def generate_name(n_id):
    short_id = str(n_id)[0:len(_syllables):]
    name = ""

    for i in range(len(short_id)):
        j = int(short_id[i]) % len(_syllables[i])
        name += _syllables[i][j]
    return name


_syllables = [
        ["Fu", "I", "Je", "Ki", "Ku", "M", "Ma", "Mo", "Na", "Ng", "Sa", "Si", "Ta", "Te", "Ti", "Zu"],
        ["", "ba", "ha", "hi", "ka", "ki", "ku", "li", "ma", "na", "ni", "si", "ta", "ti", "wa", "ya"],
        ["", "kwa", "mba", "sha"],
        ["ba", "go", "ji", "ita", "la", "mi", "ne", "ni", "nyi", "ra", "ri", "si", "tu", "we", "ye", "za"]
    ]
