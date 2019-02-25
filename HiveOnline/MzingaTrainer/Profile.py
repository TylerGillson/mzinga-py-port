import datetime
import uuid
import xml.etree.ElementTree as ElementTree

from MzingaShared.Core.AI import BoardMetricWeights
from MzingaShared.Core.AI.BoardMetricWeights import BoardMetricWeights as BoardMetricWeightsCls
from MzingaShared.Core.AI import MetricWeights
from MzingaShared.Core.AI.MetricWeights import MetricWeights as MetricWeightsCls
from MzingaTrainer import EloUtils
from MzingaTrainer import GAHelpers as Ga


class Profile:
    id = None
    game_type = None
    _name = None

    generation = 0
    parent_a = None
    parent_b = None

    board_metric_weights = None
    start_metric_weights = None
    end_metric_weights = None
    creation_timestamp = None
    last_updated_timestamp = None

    wins = 0
    losses = 0
    draws = 0
    elo_rating = EloUtils.default_rating

    @property
    def name(self):
        return self._name if not (self._name is None or self._name.isspace()) else str(self.id)[0:8:]

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def total_games(self):
        return self.wins + self.losses + self.draws

    def __init__(self, i_id, name, game_type, **kwargs):
        if "generation" in kwargs and kwargs.get("generation") < 0:
            raise ValueError("Invalid generation.")

        if "parent_a" in kwargs and kwargs.get("parent_a") is None:
            raise ValueError("Invalid parent_a.")

        if "parent_b" in kwargs and kwargs.get("parent_b") is None:
            raise ValueError("Invalid parent_b.")

        if "elo_rating" in kwargs and kwargs.get("elo_rating") < EloUtils.min_rating:
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

        self.id = i_id
        self.name = name
        self.game_type = game_type

        if "board_metric_weights" in kwargs:
            self.board_metric_weights = kwargs.pop("board_metric_weights")
            self.board_metric_weights_cls = BoardMetricWeightsCls()
        if "start_metric_weights" in kwargs:
            self.start_metric_weights = kwargs.pop("start_metric_weights")
        if "end_metric_weights" in kwargs:
            self.end_metric_weights = kwargs.pop("end_metric_weights")

        self.creation_timestamp = kwargs.pop("creation_timestamp") \
            if "creation_timestamp" in kwargs else datetime.datetime.now()
        self.last_updated_timestamp = kwargs.pop("last_updated_timestamp") \
            if "last_updated_timestamp" in kwargs else datetime.datetime.now()

        if "parent_a" in kwargs:
            self.parent_a = kwargs.pop("parent_a")
        if "parent_b" in kwargs:
            self.parent_b = kwargs.pop("parent_b")

        null_parents = (self.parent_a is None) or (self.parent_b is None)
        self.generation = 0 if null_parents else kwargs.pop("generation")

        if "elo_rating" in kwargs:
            self.elo_rating = kwargs.pop("elo_rating")
        if "wins" in kwargs:
            self.wins = kwargs.pop("wins")
        if "losses" in kwargs:
            self.losses = kwargs.pop("losses")
        if "draws" in kwargs:
            self.draws = kwargs.pop("draws")

        self.bug_metric_weights_cls = MetricWeightsCls(game_type)

    def __eq__(self, other):
        return self.id == other.id

    def __repr__(self):
        return self.name

    def __hash__(self):
        return hash(self.id)

    def update_record(self, rating, result):
        if rating < EloUtils.min_rating:
            raise ValueError("Invalid rating.")

        self.elo_rating = rating

        if result == "Loss":
            self.losses += 1
        elif result == "Draw":
            self.draws += 1
        else:
            self.wins += 1

        self.update()

    def update_metric_weights(self, start_metric_weights, end_metric_weights, board_metric_weights=None):
        if start_metric_weights is None:
            raise ValueError("Invalid start_metric_weights.")
        if end_metric_weights is None:
            raise ValueError("Invalid end_metric_weights.")

        self.start_metric_weights = start_metric_weights
        self.end_metric_weights = end_metric_weights

        if board_metric_weights is not None:
            self.board_metric_weights = board_metric_weights

        self.update()

    def update(self):
        self.last_updated_timestamp = datetime.datetime.now()

    def write_xml(self, output_stream):
        if output_stream is None:
            raise ValueError("Invalid output_stream.")

        root = ElementTree.Element("profile")
        ElementTree.SubElement(root, "id").text = str(self.id)

        if not (self._name is None or self._name.isspace()):
            ElementTree.SubElement(root, "name").text = self._name.strip()
        if self.parent_a is not None:
            ElementTree.SubElement(root, "parent_a").text = str(self.parent_a)
        if self.parent_b is not None:
            ElementTree.SubElement(root, "parent_b").text = str(self.parent_b)

        ElementTree.SubElement(root, "game_type").text = str(self.game_type)
        ElementTree.SubElement(root, "elo_rating").text = str(self.elo_rating)
        ElementTree.SubElement(root, "wins").text = str(self.wins)
        ElementTree.SubElement(root, "losses").text = str(self.losses)
        ElementTree.SubElement(root, "draws").text = str(self.draws)
        ElementTree.SubElement(root, "creation").text = str(self.creation_timestamp)
        ElementTree.SubElement(root, "last_updated").text = str(self.last_updated_timestamp)

        start_metric_weights = ElementTree.SubElement(root, "start_metric_weights")
        end_metric_weights = ElementTree.SubElement(root, "end_metric_weights")

        def write_start_weights(bug_type, bug_type_weight):
            key = self.bug_metric_weights_cls.get_key_name(bug_type, bug_type_weight)
            w_value = self.start_metric_weights.get(bug_type, bug_type_weight)
            ElementTree.SubElement(parent_node, key).text = str(w_value)

        def write_end_weights(bug_type, bug_type_weight):
            key = self.bug_metric_weights_cls.get_key_name(bug_type, bug_type_weight)
            w_value = self.end_metric_weights.get(bug_type, bug_type_weight)
            ElementTree.SubElement(parent_node, key).text = str(w_value)

        parent_node = start_metric_weights
        self.bug_metric_weights_cls.iterate_over_weights(write_start_weights)

        parent_node = end_metric_weights
        self.bug_metric_weights_cls.iterate_over_weights(write_end_weights)

        if self.game_type == "Extended":
            board_metric_weights = ElementTree.SubElement(root, "board_metric_weights")

            def write_board_weights(key):
                w_value = self.board_metric_weights.get(key)
                ElementTree.SubElement(parent_node, key).text = str(w_value)

            parent_node = board_metric_weights
            self.board_metric_weights_cls.iterate_over_weights(write_board_weights)

        tree = ElementTree.ElementTree(root)
        tree.write(output_stream)

    @staticmethod
    def read_xml(input_stream):
        if input_stream is None:
            raise ValueError("Invalid input_stream.")

        r_id = None
        r_name = None
        game_type = None
        generation = 0
        parent_a = None
        parent_b = None
        elo_rating = EloUtils.default_rating
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
            if node.tag == "id":
                r_id = uuid.UUID(uuid.UUID(node.text).hex)
            elif node.tag == "name":
                r_name = node.text
            elif node.tag == "game_type":
                game_type = node.text
            elif node.tag == "generation":
                generation = int(node.text)
            elif node.tag == "parent_a":
                parent_a = uuid.UUID(uuid.UUID(node.text).hex)
            elif node.tag == "parent_b":
                parent_b = uuid.UUID(uuid.UUID(node.text).hex)
            elif node.tag == "elo_rating":
                elo_rating = int(node.text)
            elif node.tag == "wins":
                wins = int(node.text)
            elif node.tag == "losses":
                losses = int(node.text)
            elif node.tag == "draws":
                draws = int(node.text)
            elif node.tag == "creation":
                creation_timestamp = datetime.datetime.strptime(node.text, '%Y-%m-%d %H:%M:%S.%f')
            elif node.tag == "last_updated":
                last_updated_timestamp = datetime.datetime.strptime(node.text, '%Y-%m-%d %H:%M:%S.%f')
            elif node.tag == "board_metric_weights":
                board_metric_weights = BoardMetricWeights.read_metric_weights_xml([subelem for subelem in node])
            elif node.tag in ["metric_weights", "start_metric_weights"]:
                start_metric_weights = \
                    MetricWeights.read_metric_weights_xml([subelem for subelem in node], game_type)
            elif node.tag == "end_metric_weights":
                end_metric_weights = \
                    MetricWeights.read_metric_weights_xml([subelem for subelem in node], game_type)

        if r_name is None:
            r_name = generate_name(r_id)
        if game_type is None:
            game_type = "Original"
        if end_metric_weights is None:
            end_metric_weights = start_metric_weights

        kwargs = {
            "elo_rating": elo_rating,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "start_metric_weights": start_metric_weights,
            "end_metric_weights": end_metric_weights,
            "creation_timestamp": creation_timestamp,
            "last_updated_timestamp": last_updated_timestamp,
            "generation": generation,
        }
        if parent_a is not None:
            kwargs.update({"parent_a": parent_a, "parent_b": parent_b})
        if board_metric_weights is not None:
            kwargs.update({"board_metric_weights": board_metric_weights})

        return Profile(r_id, r_name, game_type, **kwargs)

    @staticmethod
    def generate(min_weight, max_weight, game_type):
        g_id = uuid.uuid4()
        g_name = generate_name(g_id)

        start_metric_weights = Ga.generate_metric_weights(min_weight, max_weight, game_type)
        end_metric_weights = Ga.generate_metric_weights(min_weight, max_weight, game_type)

        kwargs = {
            "start_metric_weights": start_metric_weights,
            "end_metric_weights": end_metric_weights
        }
        if game_type == "Extended":
            board_metric_weights = Ga.generate_board_metric_weights(min_weight, max_weight)
            kwargs.update({"board_metric_weights": board_metric_weights})

        return Profile(g_id, g_name, game_type, **kwargs)

    @staticmethod
    def mate(parent_a, parent_b, min_mix, max_mix, use_original_ga=False):
        if parent_a is None:
            raise ValueError("Invalid parent_a.")
        if parent_b is None:
            raise ValueError("Invalid parent_b.")
        if parent_a.game_type != parent_b.game_type:
            raise ValueError("Cannot mate profiles with differing game types.")
        if min_mix > max_mix:
            raise ValueError("Invalid min/max_mixes.")

        m_id = uuid.uuid4()
        name = generate_name(m_id)
        elo_rating = EloUtils.default_rating
        generation = max(parent_a.generation, parent_b.generation) + 1
        original_rules = parent_a.game_type == "Original"

        # Normalize metric weights:
        pa_start_norm = parent_a.start_metric_weights.get_normalized()
        pa_end_norm = parent_a.end_metric_weights.get_normalized()
        pb_start_norm = parent_b.start_metric_weights.get_normalized()
        pb_end_norm = parent_b.end_metric_weights.get_normalized()

        board_metric_weights = None
        pa_board_norm = None
        pb_board_norm = None

        if not original_rules:
            pa_board_norm = parent_a.board_metric_weights.get_normalized()
            pb_board_norm = parent_b.board_metric_weights.get_normalized()

        if original_rules or use_original_ga:
            start_metric_weights = Ga.mix_metric_weights(pa_start_norm, pb_start_norm,
                                                         min_mix, max_mix, parent_a.game_type)
            end_metric_weights = Ga.mix_metric_weights(pa_end_norm, pb_end_norm,
                                                       min_mix, max_mix, parent_a.game_type)
            if use_original_ga:
                board_metric_weights = Ga.mix_board_metric_weights(pa_board_norm, pb_board_norm, min_mix, max_mix)
        else:
            start_metric_weights = Ga.cross_over(pa_start_norm, pb_start_norm)
            end_metric_weights = Ga.cross_over(pa_end_norm, pb_end_norm)
            board_metric_weights = Ga.cross_over(pa_board_norm, pb_board_norm)

            start_metric_weights = Ga.mutate(start_metric_weights)
            end_metric_weights = Ga.mutate(end_metric_weights)
            board_metric_weights = Ga.mutate(board_metric_weights)

        kwargs = {
            "generation": generation,
            "parent_a": parent_a.id,
            "parent_b": parent_b.id,
            "elo_rating": elo_rating,
            "creation_timestamp": datetime.datetime.now(),
            "start_metric_weights": start_metric_weights,
            "end_metric_weights": end_metric_weights,
        }
        if parent_a.game_type == "Extended":
            kwargs.update({"board_metric_weights": board_metric_weights})

        return Profile(m_id, name, parent_a.game_type, **kwargs)


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
