import multiprocessing
import platform
import xml.etree.ElementTree as ElementTree
from typing import Union

from MzingaShared.Core.AI import BoardMetricWeights
from MzingaShared.Core.AI import MetricWeights
from MzingaShared.Core.AI.GameAI import GameAI
from MzingaShared.Core.AI.GameAIConfig import GameAIConfig
from MzingaShared.Core.AI import TranspositionTable

is_64 = platform.architecture() == "64bit"


class GameEngineConfig:

    transposition_table_size_mb = None
    board_metric_weights = None
    start_metric_weights = None
    end_metric_weights = None
    ponder_during_idle = "Disabled"

    min_transposition_table_size_mb = 1
    max_transposition_table_size_mb_32_bit = 1024
    max_transposition_table_size_mb_64_bit = 2048

    min_max_helper_threads = 0
    max_max_helper_threads = (multiprocessing.cpu_count() // 2) - 1

    min_max_branching_factor = 1

    _max_helper_threads: Union[int, None] = None
    # Hard min is 0, hard max is (Environment.ProcessorCount / 2) - 1
    hard_max = \
        min(_max_helper_threads, max_max_helper_threads) if _max_helper_threads is not None else max_max_helper_threads
    max_helper_threads = max(min_max_helper_threads, hard_max)

    max_branching_factor = None
    report_intermediate_best_moves = False
    game_type = "Original"  # "Original"

    def __init__(self, input_stream):
        self.load_config(input_stream)

    def load_config(self, input_stream):
        if input_stream is None:
            raise ValueError("Invalid input_stream.")

        parser = ElementTree.XMLParser(encoding="utf-8")

        if isinstance(input_stream, str):
            root = ElementTree.fromstring(input_stream.strip().replace('\n', ''), parser=parser)
        else:
            reader = ElementTree.parse(input_stream, parser=parser)
            root = reader.getroot()

        if root.tag == "Mzinga.Engine":
            self.load_game_ai_config([elem for elem in root])

    def load_game_ai_config(self, xml_tree):
        if xml_tree is None:
            raise ValueError("Invalid xml_tree.")

        for node in xml_tree:
            sub_elems = [sub_elem for sub_elem in node]
            for elem in sub_elems:
                if elem.tag == "transposition_table_size_mb":
                    self.parse_transposition_table_size_mb_value(elem.text)
                if elem.tag == "board_metric_weights":
                    self.board_metric_weights = BoardMetricWeights.read_metric_weights_xml(elem)
                if elem.tag in ["metric_weights", "start_metric_weights"]:
                    self.start_metric_weights = MetricWeights.read_metric_weights_xml(elem, self.game_type)
                if elem.tag == "end_metric_weights":
                    self.end_metric_weights = MetricWeights.read_metric_weights_xml(elem, self.game_type)
                if elem.tag == "max_helper_threads":
                    self.parse_max_helper_threads_value(elem.text)
                if elem.tag == "ponder_during_idle":
                    self.parse_ponder_during_idle_value(elem.text)
                if elem.tag == "max_branching_factor":
                    self.parse_max_branching_factor_value(elem.text)
                if elem.tag == "report_intermediate_best_moves":
                    self.parse_report_intermediate_best_moves_value(elem.text)
                if elem.tag == "game_type":
                    self.parse_game_type_value(elem.text)

    def parse_transposition_table_size_mb_value(self, raw_value):
        int_value = int(raw_value)
        size = self.max_transposition_table_size_mb_64_bit if is_64 else self.max_transposition_table_size_mb_32_bit
        minimum = min(int_value, size)

        self.transposition_table_size_mb = max(self.min_transposition_table_size_mb, minimum)

    def get_transposition_table_size_mb_value(self):
        r_type = "int"

        default = TranspositionTable.default_size_in_bytes / (1024 * 1024)
        value = str(self.transposition_table_size_mb if self.transposition_table_size_mb is not None else default)

        size = self.max_transposition_table_size_mb_64_bit if is_64 else self.max_transposition_table_size_mb_32_bit
        values = "%d;%d" % (self.min_transposition_table_size_mb, size)
        return r_type, value, values

    def parse_max_helper_threads_value(self, raw_value):
        try:
            val = int(raw_value)
            self._max_helper_threads = max(self.min_max_helper_threads, min(val, self.max_max_helper_threads))
        except ValueError:
            if raw_value is None:
                self._max_helper_threads = 0
            elif raw_value == "Auto":
                self._max_helper_threads = None

    def get_max_helper_threads_value(self):
        r_type = "string"

        if self._max_helper_threads is None:
            value = "Auto"
        elif self._max_helper_threads == 0:
            value = "None"
        else:
            value = str(self._max_helper_threads)

        values = "Auto;None"

        i = 1
        while i < self.max_max_helper_threads:
            values += ";" + str(i)

        return r_type, value, values

    def parse_ponder_during_idle_value(self, raw_value):
        if raw_value in ponder_during_idleTypes:
            self.ponder_during_idle = raw_value

    def get_ponder_during_idle_value(self):
        r_type = "string"
        value = self.ponder_during_idle
        values = "Disabled;SingleThreaded;MultiThreaded"
        return r_type, value, values

    def parse_max_branching_factor_value(self, raw_value):
        try:
            val = int(raw_value)
            self.max_branching_factor = max(self.min_max_branching_factor, min(val, GameAI.max_max_branching_factor))
        except ValueError:
            pass

    def get_max_branching_factor_value(self):
        r_type = "int"
        value = \
            str(self.max_branching_factor if self.max_branching_factor is not None else GameAI.max_max_branching_factor)
        values = "%d;%d" % (self.min_max_branching_factor, GameAI.max_max_branching_factor)
        return r_type, value, values

    def parse_report_intermediate_best_moves_value(self, raw_value):
        try:
            self.report_intermediate_best_moves = raw_value == 'True'
        except ValueError:
            pass

    def get_report_intermediate_best_moves_value(self):
        r_type = "bool"
        value = str(self.report_intermediate_best_moves)
        values = ""
        return r_type, value, values

    def parse_game_type_value(self, raw_value):
        if raw_value in game_types:
            self.game_type = raw_value

    def get_game_type_value(self):
        r_type = "string"
        value = self.game_type
        values = "%s;" % game_types
        return r_type, value, values

    def get_game_ai(self):
        return GameAI("engine", config=GameAIConfig(
            self.start_metric_weights,
            self.end_metric_weights if self.end_metric_weights else self.start_metric_weights,
            self.transposition_table_size_mb,
            self.game_type,
            self.max_branching_factor,
            self.board_metric_weights,
        ))


def get_default_config(game_type):
    if game_type is None or game_type == "Original":
        return GameEngineConfig(DefaultConfig)
    elif game_type == "Extended":
        return GameEngineConfig(ExtendedConfig)


max_helper_threadsTypes = ["Auto", "None"]
ponder_during_idleTypes = ["Disabled", "SingleThreaded", "MultiThreaded"]
game_types = ["Original", "Extended"]

DefaultConfig = """
<?xml version="1.0" encoding="utf-8" ?>
<Mzinga.Engine>
<GameAI>
<transposition_table_size_mb>32</transposition_table_size_mb>
<max_helper_threads>Auto</max_helper_threads>
<ponder_during_idle>SingleThreaded</ponder_during_idle>
<report_intermediate_best_moves>False</report_intermediate_best_moves>
<game_type>Original</game_type>
<metric_weights>
<QueenBee.in_play_weight>-31.271265238491477</QueenBee.in_play_weight>
<QueenBee.is_pinned_weight>2.0334710106223222</QueenBee.is_pinned_weight>
<QueenBee.is_covered_weight>-9.4245904810096075</QueenBee.is_covered_weight>
<QueenBee.noisy_move_weight>-70.808251671610989</QueenBee.noisy_move_weight>
<QueenBee.quiet_move_weight>89.310825113084078</QueenBee.quiet_move_weight>
<QueenBee.friendly_neighbour_weight>-1292.144333086947</QueenBee.friendly_neighbour_weight>
<QueenBee.enemy_neighbour_weight>-2369.901737091086</QueenBee.enemy_neighbour_weight>
<Spider.in_play_weight>-149.30840826867541</Spider.in_play_weight>
<Spider.is_pinned_weight>40.694851291829188</Spider.is_pinned_weight>
<Spider.is_covered_weight>54.938846900842073</Spider.is_covered_weight>
<Spider.noisy_move_weight>120.6824977665965</Spider.noisy_move_weight>
<Spider.quiet_move_weight>4.237933253980211</Spider.quiet_move_weight>
<Spider.friendly_neighbour_weight>6.6842247969257773</Spider.friendly_neighbour_weight>
<Spider.enemy_neighbour_weight>-36.287365364328664</Spider.enemy_neighbour_weight>
<Beetle.in_play_weight>-21.298671861013247</Beetle.in_play_weight>
<Beetle.is_pinned_weight>44.975440006673075</Beetle.is_pinned_weight>
<Beetle.is_covered_weight>0.22640443368181792</Beetle.is_covered_weight>
<Beetle.noisy_move_weight>11.799687995838319</Beetle.noisy_move_weight>
<Beetle.quiet_move_weight>-0.41972015855122363</Beetle.quiet_move_weight>
<Beetle.friendly_neighbour_weight>-47.835946773298062</Beetle.friendly_neighbour_weight>
<Beetle.enemy_neighbour_weight>-34.152794853100922</Beetle.enemy_neighbour_weight>
<Grasshopper.in_play_weight>27.821419259296462</Grasshopper.in_play_weight>
<Grasshopper.is_pinned_weight>-9.1776263769379</Grasshopper.is_pinned_weight>
<Grasshopper.is_covered_weight>87.385857538232031</Grasshopper.is_covered_weight>
<Grasshopper.noisy_move_weight>24.3511057438334</Grasshopper.noisy_move_weight>
<Grasshopper.quiet_move_weight>10.463797931011674</Grasshopper.quiet_move_weight>
<Grasshopper.friendly_neighbour_weight>-8.5728600941518582</Grasshopper.friendly_neighbour_weight>
<Grasshopper.enemy_neighbour_weight>-15.15464964418423</Grasshopper.enemy_neighbour_weight>
<SoldierAnt.in_play_weight>14.791404237533643</SoldierAnt.in_play_weight>
<SoldierAnt.is_pinned_weight>3.5479715260690874</SoldierAnt.is_pinned_weight>
<SoldierAnt.is_covered_weight>0.86876704527939075</SoldierAnt.is_covered_weight>
<SoldierAnt.noisy_move_weight>12.544588833928383</SoldierAnt.noisy_move_weight>
<SoldierAnt.quiet_move_weight>44.651134348684522</SoldierAnt.quiet_move_weight>
<SoldierAnt.friendly_neighbour_weight>-1.0205554548560434</SoldierAnt.friendly_neighbour_weight>
<SoldierAnt.enemy_neighbour_weight>-3.7158092609214641</SoldierAnt.enemy_neighbour_weight>
</metric_weights>
</GameAI>
</Mzinga.Engine>
"""

ExtendedConfig = """
<?xml version="1.0" encoding="utf-8" ?>
<Mzinga.Engine>
<GameAI>
<transposition_table_size_mb>32</transposition_table_size_mb>
<max_helper_threads>Auto</max_helper_threads>
<ponder_during_idle>SingleThreaded</ponder_during_idle>
<report_intermediate_best_moves>False</report_intermediate_best_moves>
<game_type>Extended</game_type>
<start_metric_weights>
<QueenBee.in_play_weight>-13.575948</QueenBee.in_play_weight>
<QueenBee.is_pinned_weight>-11.390854</QueenBee.is_pinned_weight>
<QueenBee.is_covered_weight>65.871924</QueenBee.is_covered_weight>
<QueenBee.noisy_move_weight>8.069638</QueenBee.noisy_move_weight>
<QueenBee.quiet_move_weight>84.280936</QueenBee.quiet_move_weight>
<QueenBee.friendly_neighbour_weight>-29.429172</QueenBee.friendly_neighbour_weight>
<QueenBee.enemy_neighbour_weight>98.584215</QueenBee.enemy_neighbour_weight>
<QueenBee.can_make_noisy_ring_weight>68.978802</QueenBee.can_make_noisy_ring_weight>
<QueenBee.can_make_defense_ring_weight>86.83239</QueenBee.can_make_defense_ring_weight>
<Spider.in_play_weight>34.591204</Spider.in_play_weight>
<Spider.is_pinned_weight>-86.090283</Spider.is_pinned_weight>
<Spider.is_covered_weight>39.236924</Spider.is_covered_weight>
<Spider.noisy_move_weight>48.535448</Spider.noisy_move_weight>
<Spider.quiet_move_weight>-23.165922</Spider.quiet_move_weight>
<Spider.friendly_neighbour_weight>81.861833</Spider.friendly_neighbour_weight>
<Spider.enemy_neighbour_weight>-86.82599</Spider.enemy_neighbour_weight>
<Spider.can_make_noisy_ring_weight>62.860191</Spider.can_make_noisy_ring_weight>
<Spider.can_make_defense_ring_weight>49.088142</Spider.can_make_defense_ring_weight>
<Beetle.in_play_weight>91.830788</Beetle.in_play_weight>
<Beetle.is_pinned_weight>-29.980104</Beetle.is_pinned_weight>
<Beetle.is_covered_weight>-33.974149</Beetle.is_covered_weight>
<Beetle.noisy_move_weight>45.268098</Beetle.noisy_move_weight>
<Beetle.quiet_move_weight>3.037637</Beetle.quiet_move_weight>
<Beetle.friendly_neighbour_weight>56.283969</Beetle.friendly_neighbour_weight>
<Beetle.enemy_neighbour_weight>-39.481233</Beetle.enemy_neighbour_weight>
<Beetle.can_make_noisy_ring_weight>-5.302477</Beetle.can_make_noisy_ring_weight>
<Beetle.can_make_defense_ring_weight>-34.094779</Beetle.can_make_defense_ring_weight>
<Grasshopper.in_play_weight>73.91689</Grasshopper.in_play_weight>
<Grasshopper.is_pinned_weight>34.643755</Grasshopper.is_pinned_weight>
<Grasshopper.is_covered_weight>-25.890344</Grasshopper.is_covered_weight>
<Grasshopper.noisy_move_weight>-100.0</Grasshopper.noisy_move_weight>
<Grasshopper.quiet_move_weight>44.152274</Grasshopper.quiet_move_weight>
<Grasshopper.friendly_neighbour_weight>-4.827278</Grasshopper.friendly_neighbour_weight>
<Grasshopper.enemy_neighbour_weight>-6.603112</Grasshopper.enemy_neighbour_weight>
<Grasshopper.can_make_noisy_ring_weight>53.988895</Grasshopper.can_make_noisy_ring_weight>
<Grasshopper.can_make_defense_ring_weight>-83.655425</Grasshopper.can_make_defense_ring_weight>
<SoldierAnt.in_play_weight>-88.959255</SoldierAnt.in_play_weight>
<SoldierAnt.is_pinned_weight>-78.526155</SoldierAnt.is_pinned_weight>
<SoldierAnt.is_covered_weight>36.125556</SoldierAnt.is_covered_weight>
<SoldierAnt.noisy_move_weight>32.181814</SoldierAnt.noisy_move_weight>
<SoldierAnt.quiet_move_weight>-22.149079</SoldierAnt.quiet_move_weight>
<SoldierAnt.friendly_neighbour_weight>82.587752</SoldierAnt.friendly_neighbour_weight>
<SoldierAnt.enemy_neighbour_weight>76.401599</SoldierAnt.enemy_neighbour_weight>
<SoldierAnt.can_make_noisy_ring_weight>62.448668</SoldierAnt.can_make_noisy_ring_weight>
<SoldierAnt.can_make_defense_ring_weight>-61.770531</SoldierAnt.can_make_defense_ring_weight>
</start_metric_weights>
<end_metric_weights>
<QueenBee.in_play_weight>35.977407</QueenBee.in_play_weight>
<QueenBee.is_pinned_weight>16.526246</QueenBee.is_pinned_weight>
<QueenBee.is_covered_weight>-25.635449</QueenBee.is_covered_weight>
<QueenBee.noisy_move_weight>67.72225</QueenBee.noisy_move_weight>
<QueenBee.quiet_move_weight>-92.177098</QueenBee.quiet_move_weight>
<QueenBee.friendly_neighbour_weight>94.246805</QueenBee.friendly_neighbour_weight>
<QueenBee.enemy_neighbour_weight>78.519884</QueenBee.enemy_neighbour_weight>
<QueenBee.can_make_noisy_ring_weight>46.350363</QueenBee.can_make_noisy_ring_weight>
<QueenBee.can_make_defense_ring_weight>49.049371</QueenBee.can_make_defense_ring_weight>
<Spider.in_play_weight>73.087661</Spider.in_play_weight>
<Spider.is_pinned_weight>-95.344391</Spider.is_pinned_weight>
<Spider.is_covered_weight>-78.142462</Spider.is_covered_weight>
<Spider.noisy_move_weight>77.606477</Spider.noisy_move_weight>
<Spider.quiet_move_weight>-86.043358</Spider.quiet_move_weight>
<Spider.friendly_neighbour_weight>67.159172</Spider.friendly_neighbour_weight>
<Spider.enemy_neighbour_weight>76.46847</Spider.enemy_neighbour_weight>
<Spider.can_make_noisy_ring_weight>52.907164</Spider.can_make_noisy_ring_weight>
<Spider.can_make_defense_ring_weight>-43.476861</Spider.can_make_defense_ring_weight>
<Beetle.in_play_weight>-65.946415</Beetle.in_play_weight>
<Beetle.is_pinned_weight>-15.997796</Beetle.is_pinned_weight>
<Beetle.is_covered_weight>-42.647107</Beetle.is_covered_weight>
<Beetle.noisy_move_weight>35.069179</Beetle.noisy_move_weight>
<Beetle.quiet_move_weight>64.975771</Beetle.quiet_move_weight>
<Beetle.friendly_neighbour_weight>-24.944331</Beetle.friendly_neighbour_weight>
<Beetle.enemy_neighbour_weight>-95.038815</Beetle.enemy_neighbour_weight>
<Beetle.can_make_noisy_ring_weight>5.986062</Beetle.can_make_noisy_ring_weight>
<Beetle.can_make_defense_ring_weight>-2.666235</Beetle.can_make_defense_ring_weight>
<Grasshopper.in_play_weight>-47.801049</Grasshopper.in_play_weight>
<Grasshopper.is_pinned_weight>-95.793614</Grasshopper.is_pinned_weight>
<Grasshopper.is_covered_weight>100.0</Grasshopper.is_covered_weight>
<Grasshopper.noisy_move_weight>-84.792599</Grasshopper.noisy_move_weight>
<Grasshopper.quiet_move_weight>-24.045674</Grasshopper.quiet_move_weight>
<Grasshopper.friendly_neighbour_weight>0.361557</Grasshopper.friendly_neighbour_weight>
<Grasshopper.enemy_neighbour_weight>3.507716</Grasshopper.enemy_neighbour_weight>
<Grasshopper.can_make_noisy_ring_weight>-62.631449</Grasshopper.can_make_noisy_ring_weight>
<Grasshopper.can_make_defense_ring_weight>94.998452</Grasshopper.can_make_defense_ring_weight>
<SoldierAnt.in_play_weight>53.042894</SoldierAnt.in_play_weight>
<SoldierAnt.is_pinned_weight>-90.892167</SoldierAnt.is_pinned_weight>
<SoldierAnt.is_covered_weight>89.260138</SoldierAnt.is_covered_weight>
<SoldierAnt.noisy_move_weight>40.773407</SoldierAnt.noisy_move_weight>
<SoldierAnt.quiet_move_weight>30.516268</SoldierAnt.quiet_move_weight>
<SoldierAnt.friendly_neighbour_weight>60.189976</SoldierAnt.friendly_neighbour_weight>
<SoldierAnt.enemy_neighbour_weight>-53.657924</SoldierAnt.enemy_neighbour_weight>
<SoldierAnt.can_make_noisy_ring_weight>-0.428643</SoldierAnt.can_make_noisy_ring_weight>
<SoldierAnt.can_make_defense_ring_weight>92.386741</SoldierAnt.can_make_defense_ring_weight>
</end_metric_weights>
<board_metric_weights>
<queen_bee_life_weight>81.590604</queen_bee_life_weight>
<queen_bee_tight_spaces_weight>36.176612</queen_bee_tight_spaces_weight>
<noisy_ring_weight>-98.0</noisy_ring_weight>
</board_metric_weights>
</GameAI>
</Mzinga.Engine>
"""
