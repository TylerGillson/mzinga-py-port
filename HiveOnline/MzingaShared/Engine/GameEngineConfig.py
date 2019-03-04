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
<QueenBee.in_play_weight>-53.283794</QueenBee.in_play_weight>
<QueenBee.is_pinned_weight>48.324673</QueenBee.is_pinned_weight>
<QueenBee.is_covered_weight>-47.263218</QueenBee.is_covered_weight>
<QueenBee.noisy_move_weight>-10.980133</QueenBee.noisy_move_weight>
<QueenBee.quiet_move_weight>44.052035</QueenBee.quiet_move_weight>
<QueenBee.friendly_neighbour_weight>-54.222968</QueenBee.friendly_neighbour_weight>
<QueenBee.enemy_neighbour_weight>84.45407</QueenBee.enemy_neighbour_weight>
<QueenBee.can_make_noisy_ring_weight>24.221056</QueenBee.can_make_noisy_ring_weight>
<QueenBee.can_make_defense_ring_weight>77.276648</QueenBee.can_make_defense_ring_weight>
<Spider.in_play_weight>-56.649913</Spider.in_play_weight>
<Spider.is_pinned_weight>-84.960595</Spider.is_pinned_weight>
<Spider.is_covered_weight>15.09315</Spider.is_covered_weight>
<Spider.noisy_move_weight>35.685473</Spider.noisy_move_weight>
<Spider.quiet_move_weight>46.923498</Spider.quiet_move_weight>
<Spider.friendly_neighbour_weight>-26.900277</Spider.friendly_neighbour_weight>
<Spider.enemy_neighbour_weight>41.386314</Spider.enemy_neighbour_weight>
<Spider.can_make_noisy_ring_weight>-53.693788</Spider.can_make_noisy_ring_weight>
<Spider.can_make_defense_ring_weight>72.334669</Spider.can_make_defense_ring_weight>
<Beetle.in_play_weight>24.235901</Beetle.in_play_weight>
<Beetle.is_pinned_weight>18.590718</Beetle.is_pinned_weight>
<Beetle.is_covered_weight>69.431712</Beetle.is_covered_weight>
<Beetle.noisy_move_weight>-4.644623</Beetle.noisy_move_weight>
<Beetle.quiet_move_weight>-2.723748</Beetle.quiet_move_weight>
<Beetle.friendly_neighbour_weight>-25.635257</Beetle.friendly_neighbour_weight>
<Beetle.enemy_neighbour_weight>12.509768</Beetle.enemy_neighbour_weight>
<Beetle.can_make_noisy_ring_weight>50.111024</Beetle.can_make_noisy_ring_weight>
<Beetle.can_make_defense_ring_weight>51.912852</Beetle.can_make_defense_ring_weight>
<Grasshopper.in_play_weight>26.663546</Grasshopper.in_play_weight>
<Grasshopper.is_pinned_weight>91.346694</Grasshopper.is_pinned_weight>
<Grasshopper.is_covered_weight>82.527572</Grasshopper.is_covered_weight>
<Grasshopper.noisy_move_weight>87.756318</Grasshopper.noisy_move_weight>
<Grasshopper.quiet_move_weight>-100.0</Grasshopper.quiet_move_weight>
<Grasshopper.friendly_neighbour_weight>-46.693734</Grasshopper.friendly_neighbour_weight>
<Grasshopper.enemy_neighbour_weight>-48.989205</Grasshopper.enemy_neighbour_weight>
<Grasshopper.can_make_noisy_ring_weight>-59.750578</Grasshopper.can_make_noisy_ring_weight>
<Grasshopper.can_make_defense_ring_weight>-82.654857</Grasshopper.can_make_defense_ring_weight>
<SoldierAnt.in_play_weight>-21.228194</SoldierAnt.in_play_weight>
<SoldierAnt.is_pinned_weight>9.747632</SoldierAnt.is_pinned_weight>
<SoldierAnt.is_covered_weight>-94.106845</SoldierAnt.is_covered_weight>
<SoldierAnt.noisy_move_weight>27.442806</SoldierAnt.noisy_move_weight>
<SoldierAnt.quiet_move_weight>-76.664913</SoldierAnt.quiet_move_weight>
<SoldierAnt.friendly_neighbour_weight>-83.170429</SoldierAnt.friendly_neighbour_weight>
<SoldierAnt.enemy_neighbour_weight>75.085361</SoldierAnt.enemy_neighbour_weight>
<SoldierAnt.can_make_noisy_ring_weight>-33.412931</SoldierAnt.can_make_noisy_ring_weight>
<SoldierAnt.can_make_defense_ring_weight>77.261474</SoldierAnt.can_make_defense_ring_weight>
</start_metric_weights>
<end_metric_weights>
<QueenBee.in_play_weight>-56.542985</QueenBee.in_play_weight>
<QueenBee.is_pinned_weight>91.779471</QueenBee.is_pinned_weight>
<QueenBee.is_covered_weight>62.996725</QueenBee.is_covered_weight>
<QueenBee.noisy_move_weight>41.067924</QueenBee.noisy_move_weight>
<QueenBee.quiet_move_weight>-30.168026</QueenBee.quiet_move_weight>
<QueenBee.friendly_neighbour_weight>100.0</QueenBee.friendly_neighbour_weight>
<QueenBee.enemy_neighbour_weight>-16.029684</QueenBee.enemy_neighbour_weight>
<QueenBee.can_make_noisy_ring_weight>-88.838185</QueenBee.can_make_noisy_ring_weight>
<QueenBee.can_make_defense_ring_weight>61.119177</QueenBee.can_make_defense_ring_weight>
<Spider.in_play_weight>88.534739</Spider.in_play_weight>
<Spider.is_pinned_weight>44.325434</Spider.is_pinned_weight>
<Spider.is_covered_weight>-94.415713</Spider.is_covered_weight>
<Spider.noisy_move_weight>-70.830088</Spider.noisy_move_weight>
<Spider.quiet_move_weight>45.770104</Spider.quiet_move_weight>
<Spider.friendly_neighbour_weight>60.606591</Spider.friendly_neighbour_weight>
<Spider.enemy_neighbour_weight>-78.53729</Spider.enemy_neighbour_weight>
<Spider.can_make_noisy_ring_weight>3.735779</Spider.can_make_noisy_ring_weight>
<Spider.can_make_defense_ring_weight>5.323294</Spider.can_make_defense_ring_weight>
<Beetle.in_play_weight>62.522654</Beetle.in_play_weight>
<Beetle.is_pinned_weight>35.675108</Beetle.is_pinned_weight>
<Beetle.is_covered_weight>64.551772</Beetle.is_covered_weight>
<Beetle.noisy_move_weight>-77.570721</Beetle.noisy_move_weight>
<Beetle.quiet_move_weight>27.437656</Beetle.quiet_move_weight>
<Beetle.friendly_neighbour_weight>-56.347714</Beetle.friendly_neighbour_weight>
<Beetle.enemy_neighbour_weight>-67.747492</Beetle.enemy_neighbour_weight>
<Beetle.can_make_noisy_ring_weight>-97.520286</Beetle.can_make_noisy_ring_weight>
<Beetle.can_make_defense_ring_weight>-45.700004</Beetle.can_make_defense_ring_weight>
<Grasshopper.in_play_weight>66.658697</Grasshopper.in_play_weight>
<Grasshopper.is_pinned_weight>-43.231783</Grasshopper.is_pinned_weight>
<Grasshopper.is_covered_weight>-78.290562</Grasshopper.is_covered_weight>
<Grasshopper.noisy_move_weight>91.746897</Grasshopper.noisy_move_weight>
<Grasshopper.quiet_move_weight>-97.63794</Grasshopper.quiet_move_weight>
<Grasshopper.friendly_neighbour_weight>-49.201487</Grasshopper.friendly_neighbour_weight>
<Grasshopper.enemy_neighbour_weight>65.718483</Grasshopper.enemy_neighbour_weight>
<Grasshopper.can_make_noisy_ring_weight>47.938066</Grasshopper.can_make_noisy_ring_weight>
<Grasshopper.can_make_defense_ring_weight>9.037399</Grasshopper.can_make_defense_ring_weight>
<SoldierAnt.in_play_weight>-78.558486</SoldierAnt.in_play_weight>
<SoldierAnt.is_pinned_weight>41.015719</SoldierAnt.is_pinned_weight>
<SoldierAnt.is_covered_weight>-82.66695</SoldierAnt.is_covered_weight>
<SoldierAnt.noisy_move_weight>-2.51218</SoldierAnt.noisy_move_weight>
<SoldierAnt.quiet_move_weight>-9.553079</SoldierAnt.quiet_move_weight>
<SoldierAnt.friendly_neighbour_weight>-7.773051</SoldierAnt.friendly_neighbour_weight>
<SoldierAnt.enemy_neighbour_weight>-73.07303</SoldierAnt.enemy_neighbour_weight>
<SoldierAnt.can_make_noisy_ring_weight>11.866348</SoldierAnt.can_make_noisy_ring_weight>
<SoldierAnt.can_make_defense_ring_weight>78.207316</SoldierAnt.can_make_defense_ring_weight>
</end_metric_weights>
<board_metric_weights>
<queen_bee_life_weight>-100.0</queen_bee_life_weight>
<queen_bee_tight_spaces_weight>-24.603304</queen_bee_tight_spaces_weight>
<noisy_ring_weight>110.0</noisy_ring_weight>
</board_metric_weights>
</GameAI>
</Mzinga.Engine>
"""
