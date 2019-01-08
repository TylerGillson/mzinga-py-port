import datetime
import random
import uuid
import xml.etree.ElementTree as ElementTree

from MzingaShared.Core.AI import BoardMetricWeights
from MzingaShared.Core.AI.BoardMetricWeights import BoardMetricWeights as BoardMetricWeightsCls
from MzingaShared.Core.AI import MetricWeights
from MzingaShared.Core.AI.MetricWeights import MetricWeights as MetricWeightsCls
from MzingaTrainer import EloUtils


class Profile:
    Id = None
    _name = None
    _random = None

    Generation = 0
    ParentA = None
    ParentB = None

    BoardMetricWeights = None
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

    def __init__(self, i_id, name, board_metric_weights, start_metric_weights, end_metric_weights, game_type, **kwargs):
        if "generation" in kwargs and kwargs.get("generation") < 0:
            raise ValueError("Invalid generation.")

        if "parent_a" in kwargs and kwargs.get("parent_a") is None:
            raise ValueError("Invalid parent_a.")

        if "parent_b" in kwargs and kwargs.get("parent_b") is None:
            raise ValueError("Invalid parent_b.")

        if "elo_rating" in kwargs and kwargs.get("elo_rating") < EloUtils.MinRating:
            raise ValueError("Invalid elo_rating.")

        if "board_metric_weights" in kwargs and kwargs.get("board_metric_weights") is None:
            raise ValueError("Invalid board_metric_weights.")

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

        self.BoardMetricWeights = board_metric_weights
        self.StartMetricWeights = start_metric_weights
        self.EndMetricWeights = end_metric_weights
        self.CreationTimestamp = kwargs.pop("creation_timestamp") \
            if "creation_timestamp" in kwargs else datetime.datetime.now()
        self.LastUpdatedTimestamp = kwargs.pop("last_updated_timestamp") \
            if "last_updated_timestamp" in kwargs else datetime.datetime.now()

        if "parent_a" in kwargs:
            self.ParentA = kwargs.pop("parent_a")
        if "parent_b" in kwargs:
            self.ParentB = kwargs.pop("parent_b")

        null_parents = (self.ParentA is None) or (self.ParentB is None)
        self.Generation = 0 if null_parents else kwargs.pop("generation")

        if "elo_rating" in kwargs:
            self.EloRating = kwargs.pop("elo_rating")
        if "wins" in kwargs:
            self.Wins = kwargs.pop("wins")
        if "losses" in kwargs:
            self.Losses = kwargs.pop("losses")
        if "draws" in kwargs:
            self.Draws = kwargs.pop("draws")

        self.game_type = game_type
        self.board_metric_weights_cls = BoardMetricWeightsCls()
        self.bug_metric_weights_cls = MetricWeightsCls(game_type)

    def __eq__(self, other):
        return self.Id == other.Id

    def __repr__(self):
        return self.Name

    def __hash__(self):
        return hash(self.Id)

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

    def update_metric_weights(self, board_metric_weights, start_metric_weights, end_metric_weights):
        if board_metric_weights is None:
            raise ValueError("Invalid board_metric_weights.")
        if start_metric_weights is None:
            raise ValueError("Invalid start_metric_weights.")
        if end_metric_weights is None:
            raise ValueError("Invalid end_metric_weights.")

        self.BoardMetricWeights = board_metric_weights
        self.StartMetricWeights = start_metric_weights
        self.EndMetricWeights = end_metric_weights
        self.update()

    def update(self):
        self.LastUpdatedTimestamp = datetime.datetime.now()

    def write_xml(self, output_stream):
        if output_stream is None:
            raise ValueError("Invalid output_stream.")

        root = ElementTree.Element("Profile")
        ElementTree.SubElement(root, "Id").text = str(self.Id)

        if not (self._name is None or self._name.isspace()):
            ElementTree.SubElement(root, "Name").text = self._name.strip()
        if self.ParentA is not None:
            ElementTree.SubElement(root, "ParentA").text = str(self.ParentA)
        if self.ParentB is not None:
            ElementTree.SubElement(root, "ParentB").text = str(self.ParentB)

        ElementTree.SubElement(root, "EloRating").text = str(self.EloRating)
        ElementTree.SubElement(root, "Wins").text = str(self.Wins)
        ElementTree.SubElement(root, "Losses").text = str(self.Losses)
        ElementTree.SubElement(root, "Draws").text = str(self.Draws)
        ElementTree.SubElement(root, "Creation").text = str(self.CreationTimestamp)
        ElementTree.SubElement(root, "LastUpdated").text = str(self.LastUpdatedTimestamp)

        board_metric_weights = ElementTree.SubElement(root, "BoardMetricWeights")
        start_metric_weights = ElementTree.SubElement(root, "StartMetricWeights")
        end_metric_weights = ElementTree.SubElement(root, "EndMetricWeights")

        def write_board_weights(key):
            w_value = self.BoardMetricWeights.get(key)
            ElementTree.SubElement(parent_node, key).text = str(w_value)

        def write_start_weights(bug_type, bug_type_weight):
            key = self.bug_metric_weights_cls.get_key_name(bug_type, bug_type_weight)
            w_value = self.StartMetricWeights.get(bug_type, bug_type_weight)
            ElementTree.SubElement(parent_node, key).text = str(w_value)

        def write_end_weights(bug_type, bug_type_weight):
            key = self.bug_metric_weights_cls.get_key_name(bug_type, bug_type_weight)
            w_value = self.EndMetricWeights.get(bug_type, bug_type_weight)
            ElementTree.SubElement(parent_node, key).text = str(w_value)

        parent_node = board_metric_weights
        self.board_metric_weights_cls.iterate_over_weights(write_board_weights)

        parent_node = start_metric_weights
        self.bug_metric_weights_cls.iterate_over_weights(write_start_weights)

        parent_node = end_metric_weights
        self.bug_metric_weights_cls.iterate_over_weights(write_end_weights)

        tree = ElementTree.ElementTree(root)
        tree.write(output_stream)

    def read_xml(self, input_stream):
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
        board_metric_weights = None
        start_metric_weights = None
        end_metric_weights = None
        creation_timestamp = datetime.datetime.now()
        last_updated_timestamp = creation_timestamp

        parser = ElementTree.XMLParser(encoding="utf-8")
        tree = ElementTree.parse(input_stream, parser=parser)
        root = tree.getroot()

        for node in root:
            if node.tag == "Id":
                r_id = uuid.UUID(uuid.UUID(node.text).hex)
            elif node.tag == "Name":
                r_name = node.text
            elif node.tag == "Generation":
                generation = int(node.text)
            elif node.tag == "ParentA":
                parent_a = uuid.UUID(uuid.UUID(node.text).hex)
            elif node.tag == "ParentB":
                parent_b = uuid.UUID(uuid.UUID(node.text).hex)
            elif node.tag == "EloRating":
                elo_rating = int(node.text)
            elif node.tag == "Wins":
                wins = int(node.text)
            elif node.tag == "Losses":
                losses = int(node.text)
            elif node.tag == "Draws":
                draws = int(node.text)
            elif node.tag == "Creation":
                creation_timestamp = datetime.datetime.strptime(node.text, '%Y-%m-%d %H:%M:%S.%f')
            elif node.tag == "LastUpdated":
                last_updated_timestamp = datetime.datetime.strptime(node.text, '%Y-%m-%d %H:%M:%S.%f')
            elif node.tag == "BoardMetricWeights":
                board_metric_weights = BoardMetricWeights.read_metric_weights_xml([subelem for subelem in node])
            elif node.tag in ["MetricWeights", "StartMetricWeights"]:
                start_metric_weights = \
                    MetricWeights.read_metric_weights_xml([subelem for subelem in node], self.game_type)
            elif node.tag == "EndMetricWeights":
                end_metric_weights = \
                    MetricWeights.read_metric_weights_xml([subelem for subelem in node], self.game_type)

        if r_name is None:
            r_name = generate_name(r_id)
        if end_metric_weights is None:
            end_metric_weights = start_metric_weights

        kwargs = {
            "elo_rating": elo_rating,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "board_metric_weights": board_metric_weights,
            "start_metric_weights": start_metric_weights,
            "end_metric_weights": end_metric_weights,
            "creation_timestamp": creation_timestamp,
            "last_updated_timestamp": last_updated_timestamp,
            "generation": generation,
        }
        if parent_a is not None:
            kwargs.update({"parent_a": parent_a, "parent_b": parent_b})

        return Profile(r_id, r_name, **kwargs)

    def generate(self, min_weight, max_weight):
        board_metric_weights = generate_board_metric_weights(min_weight, max_weight)
        start_metric_weights = generate_metric_weights(min_weight, max_weight, self.game_type)
        end_metric_weights = generate_metric_weights(min_weight, max_weight, self.game_type)

        g_id = uuid.uuid4()
        g_name = generate_name(g_id)

        return Profile(g_id, g_name, board_metric_weights, start_metric_weights, end_metric_weights, self.game_type)

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

        board_metric_weights = mix_board_metric_weights(
            parent_a.BoardMetricWeights.get_normalized(),
            parent_b.BoardMetricWeights.get_normalized(),
            min_mix, max_mix)

        start_metric_weights = mix_metric_weights(
            parent_a.StartMetricWeights.get_normalized(),
            parent_b.StartMetricWeights.get_normalized(),
            min_mix, max_mix, parent_a.game_type)

        end_metric_weights = mix_metric_weights(
            parent_a.EndMetricWeights.get_normalized(),
            parent_b.EndMetricWeights.get_normalized(),
            min_mix, max_mix, parent_a.game_type)

        creation_timestamp = datetime.datetime.now()

        kwargs = {
            "generation": generation,
            "parent_a": parent_a.Id,
            "parent_b": parent_b.Id,
            "elo_rating": elo_rating,
            "creation_timestamp": creation_timestamp
        }
        return Profile(m_id, name,
                       board_metric_weights, start_metric_weights, end_metric_weights,
                       parent_a.game_type, **kwargs)


def generate_board_metric_weights(min_weight, max_weight):
    bmw = BoardMetricWeightsCls()

    def generate_weights(key):
        value = min_weight + (random.random() * (max_weight - min_weight))
        bmw.set(key, value)

    bmw.iterate_over_weights(generate_weights)
    return bmw


def generate_metric_weights(min_weight, max_weight, game_type):
    mw = MetricWeightsCls(game_type)

    def generate_weights(bug_type, bug_type_weight):
        value = min_weight + (random.random() * (max_weight - min_weight))
        mw.set(bug_type, bug_type_weight, value)

    mw.iterate_over_weights(generate_weights)
    return mw


def mix_board_metric_weights(bmw_a, bmw_b, min_mix, max_mix):
    bmw = BoardMetricWeightsCls()

    def mix_weights(key):
        value = 0.5 * (bmw_a.get(key) + bmw_b.get(key))
        if value == 0.0:
            value = -0.01 + (random.random() * 0.02)
        value = value * (min_mix + (random.random() * abs(max_mix - min_mix)))
        bmw.set(key, value)

    bmw.iterate_over_weights(mix_weights)
    return bmw


def mix_metric_weights(mw_a, mw_b, min_mix, max_mix, game_type):
    mw = MetricWeightsCls(game_type)

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
        j = (ord(short_id[i]) % 9) % len(_syllables[i])
        name += _syllables[i][j]
    return name


_syllables = [
        ["Fu", "I", "Je", "Ki", "Ku", "M", "Ma", "Mo", "Na", "Ng", "Sa", "Si", "Ta", "Te", "Ti", "Zu"],
        ["", "ba", "ha", "hi", "ka", "ki", "ku", "li", "ma", "na", "ni", "si", "ta", "ti", "wa", "ya"],
        ["", "kwa", "mba", "sha"],
        ["ba", "go", "ji", "ita", "la", "mi", "ne", "ni", "nyi", "ra", "ri", "si", "tu", "we", "ye", "za"]
    ]
