﻿import multiprocessing
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
        return GameAI(GameAIConfig(
            self.start_metric_weights,
            self.end_metric_weights if self.end_metric_weights else self.start_metric_weights,
            self.transposition_table_size_mb,
            self.game_type,
            self.max_branching_factor,
            self.board_metric_weights,
        ))


def get_default_config():
    if GameEngineConfig.game_type == "Original":
        return GameEngineConfig(DefaultConfig)
    elif GameEngineConfig.game_type == "Extended":
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
<QueenBee.in_play_weight>-55.179546713569174</QueenBee.in_play_weight>
<QueenBee.is_pinned_weight>28.475971754967134</QueenBee.is_pinned_weight>
<QueenBee.is_covered_weight>57.90903052046633</QueenBee.is_covered_weight>
<QueenBee.noisy_move_weight>-77.66603481678584</QueenBee.noisy_move_weight>
<QueenBee.quiet_move_weight>-40.64368074913687</QueenBee.quiet_move_weight>
<QueenBee.friendly_neighbour_weight>-0.8099628656010935</QueenBee.friendly_neighbour_weight>
<QueenBee.enemy_neighbour_weight>68.92460220643193</QueenBee.enemy_neighbour_weight>
<QueenBee.can_make_noisy_ring_weight>-0.4275429192289266</QueenBee.can_make_noisy_ring_weight>
<QueenBee.can_make_defense_ring_weight>17.10599213126642</QueenBee.can_make_defense_ring_weight>
<Spider.in_play_weight>-50.82768969355263</Spider.in_play_weight>
<Spider.is_pinned_weight>-91.21027615673354</Spider.is_pinned_weight>
<Spider.is_covered_weight>49.12604989558423</Spider.is_covered_weight>
<Spider.noisy_move_weight>51.98768041898819</Spider.noisy_move_weight>
<Spider.quiet_move_weight>51.48793778905926</Spider.quiet_move_weight>
<Spider.friendly_neighbour_weight>36.857880350417446</Spider.friendly_neighbour_weight>
<Spider.enemy_neighbour_weight>-62.54130378115521</Spider.enemy_neighbour_weight>
<Spider.can_make_noisy_ring_weight>-24.420937822936935</Spider.can_make_noisy_ring_weight>
<Spider.can_make_defense_ring_weight>-50.95398089911547</Spider.can_make_defense_ring_weight>
<Beetle.in_play_weight>-24.089891267590417</Beetle.in_play_weight>
<Beetle.is_pinned_weight>-52.23149526959921</Beetle.is_pinned_weight>
<Beetle.is_covered_weight>96.87455412353356</Beetle.is_covered_weight>
<Beetle.noisy_move_weight>29.832911582662206</Beetle.noisy_move_weight>
<Beetle.quiet_move_weight>69.6402329360794</Beetle.quiet_move_weight>
<Beetle.friendly_neighbour_weight>12.00489743591416</Beetle.friendly_neighbour_weight>
<Beetle.enemy_neighbour_weight>-37.66814863261854</Beetle.enemy_neighbour_weight>
<Beetle.can_make_noisy_ring_weight>48.79657841384241</Beetle.can_make_noisy_ring_weight>
<Beetle.can_make_defense_ring_weight>67.03923304885978</Beetle.can_make_defense_ring_weight>
<Grasshopper.in_play_weight>-76.36081040482192</Grasshopper.in_play_weight>
<Grasshopper.is_pinned_weight>11.728428011317831</Grasshopper.is_pinned_weight>
<Grasshopper.is_covered_weight>52.21323540402267</Grasshopper.is_covered_weight>
<Grasshopper.noisy_move_weight>30.515094443054807</Grasshopper.noisy_move_weight>
<Grasshopper.quiet_move_weight>-85.62281170749739</Grasshopper.quiet_move_weight>
<Grasshopper.friendly_neighbour_weight>62.005286574892324</Grasshopper.friendly_neighbour_weight>
<Grasshopper.enemy_neighbour_weight>-52.068466783587475</Grasshopper.enemy_neighbour_weight>
<Grasshopper.can_make_noisy_ring_weight>-24.92789746561084</Grasshopper.can_make_noisy_ring_weight>
<Grasshopper.can_make_defense_ring_weight>-11.951526963348869</Grasshopper.can_make_defense_ring_weight>
<SoldierAnt.in_play_weight>20.341897188708955</SoldierAnt.in_play_weight>
<SoldierAnt.is_pinned_weight>17.131340136376565</SoldierAnt.is_pinned_weight>
<SoldierAnt.is_covered_weight>83.51995505415852</SoldierAnt.is_covered_weight>
<SoldierAnt.noisy_move_weight>80.79521448428713</SoldierAnt.noisy_move_weight>
<SoldierAnt.quiet_move_weight>-29.506567637488516</SoldierAnt.quiet_move_weight>
<SoldierAnt.friendly_neighbour_weight>-9.02554340953013</SoldierAnt.friendly_neighbour_weight>
<SoldierAnt.enemy_neighbour_weight>-95.91673175298627</SoldierAnt.enemy_neighbour_weight>
<SoldierAnt.can_make_noisy_ring_weight>-59.79393060460063</SoldierAnt.can_make_noisy_ring_weight>
<SoldierAnt.can_make_defense_ring_weight>21.250111346240715</SoldierAnt.can_make_defense_ring_weight>
</start_metric_weights>
<end_metric_weights>
<QueenBee.in_play_weight>-21.12658974717266</QueenBee.in_play_weight>
<QueenBee.is_pinned_weight>96.82101191175633</QueenBee.is_pinned_weight>
<QueenBee.is_covered_weight>29.57188920053585</QueenBee.is_covered_weight>
<QueenBee.noisy_move_weight>-84.2159567753825</QueenBee.noisy_move_weight>
<QueenBee.quiet_move_weight>77.06118446698599</QueenBee.quiet_move_weight>
<QueenBee.friendly_neighbour_weight>-32.57193074031663</QueenBee.friendly_neighbour_weight>
<QueenBee.enemy_neighbour_weight>-55.692349025440116</QueenBee.enemy_neighbour_weight>
<QueenBee.can_make_noisy_ring_weight>-28.58368521832773</QueenBee.can_make_noisy_ring_weight>
<QueenBee.can_make_defense_ring_weight>32.01427842617099</QueenBee.can_make_defense_ring_weight>
<Spider.in_play_weight>43.72244479342197</Spider.in_play_weight>
<Spider.is_pinned_weight>-32.336655255468145</Spider.is_pinned_weight>
<Spider.is_covered_weight>30.291063619652107</Spider.is_covered_weight>
<Spider.noisy_move_weight>97.84718469613887</Spider.noisy_move_weight>
<Spider.quiet_move_weight>91.34803213787066</Spider.quiet_move_weight>
<Spider.friendly_neighbour_weight>-53.0368008469565</Spider.friendly_neighbour_weight>
<Spider.enemy_neighbour_weight>12.425637363584613</Spider.enemy_neighbour_weight>
<Spider.can_make_noisy_ring_weight>-72.92412293599521</Spider.can_make_noisy_ring_weight>
<Spider.can_make_defense_ring_weight>-32.53896063836447</Spider.can_make_defense_ring_weight>
<Beetle.in_play_weight>89.1272889156576</Beetle.in_play_weight>
<Beetle.is_pinned_weight>-71.46036176049348</Beetle.is_pinned_weight>
<Beetle.is_covered_weight>-61.04184806204602</Beetle.is_covered_weight>
<Beetle.noisy_move_weight>95.719549683184</Beetle.noisy_move_weight>
<Beetle.quiet_move_weight>85.49346923335722</Beetle.quiet_move_weight>
<Beetle.friendly_neighbour_weight>83.27466741080991</Beetle.friendly_neighbour_weight>
<Beetle.enemy_neighbour_weight>20.985123045476257</Beetle.enemy_neighbour_weight>
<Beetle.can_make_noisy_ring_weight>-37.644666795678795</Beetle.can_make_noisy_ring_weight>
<Beetle.can_make_defense_ring_weight>69.50933736226824</Beetle.can_make_defense_ring_weight>
<Grasshopper.in_play_weight>88.1263575105458</Grasshopper.in_play_weight>
<Grasshopper.is_pinned_weight>31.385750916465668</Grasshopper.is_pinned_weight>
<Grasshopper.is_covered_weight>55.01484349104459</Grasshopper.is_covered_weight>
<Grasshopper.noisy_move_weight>34.1222744861297</Grasshopper.noisy_move_weight>
<Grasshopper.quiet_move_weight>-79.92837890910359</Grasshopper.quiet_move_weight>
<Grasshopper.friendly_neighbour_weight>-15.679116093447348</Grasshopper.friendly_neighbour_weight>
<Grasshopper.enemy_neighbour_weight>-38.89096810878176</Grasshopper.enemy_neighbour_weight>
<Grasshopper.can_make_noisy_ring_weight>-63.40142541455482</Grasshopper.can_make_noisy_ring_weight>
<Grasshopper.can_make_defense_ring_weight>76.39929189845566</Grasshopper.can_make_defense_ring_weight>
<SoldierAnt.in_play_weight>44.38469520171856</SoldierAnt.in_play_weight>
<SoldierAnt.is_pinned_weight>-93.2141982760108</SoldierAnt.is_pinned_weight>
<SoldierAnt.is_covered_weight>-58.11852028075219</SoldierAnt.is_covered_weight>
<SoldierAnt.noisy_move_weight>10.607854179078302</SoldierAnt.noisy_move_weight>
<SoldierAnt.quiet_move_weight>-65.7494832769982</SoldierAnt.quiet_move_weight>
<SoldierAnt.friendly_neighbour_weight>-66.72462501762368</SoldierAnt.friendly_neighbour_weight>
<SoldierAnt.enemy_neighbour_weight>-63.11316250375769</SoldierAnt.enemy_neighbour_weight>
<SoldierAnt.can_make_noisy_ring_weight>73.09381587081336</SoldierAnt.can_make_noisy_ring_weight>
<SoldierAnt.can_make_defense_ring_weight>56.671037091972664</SoldierAnt.can_make_defense_ring_weight>
</end_metric_weights>  
<board_metric_weights>
<queen_bee_life_weight>-9.756361042183443</queen_bee_life_weight>
<queen_bee_tight_spaces_weight>18.822767443419224</queen_bee_tight_spaces_weight>
<noisy_ring_weight>-25.168072225984673</noisy_ring_weight>
</board_metric_weights>
</GameAI>
</Mzinga.Engine>
"""
