import sys
import os
from os.path import dirname
sys.path.append(dirname(dirname(os.getcwd())))  # Add root directory to PYTHONPATH

import multiprocessing
import platform
import xml.etree.ElementTree as ElementTree

from MzingaShared.Core.AI.GameAI import GameAI
from MzingaShared.Core.AI.GameAIConfig import GameAIConfig
from MzingaShared.Core.AI.MetricWeights import MetricWeights
from MzingaShared.Core.AI.TranspositionTable import TranspositionTable

is_64 = platform.architecture() == "64bit"


class GameEngineConfig:

    TranspositionTableSizeMB = None
    StartMetricWeights = None
    EndMetricWeights = None
    PonderDuringIdle = "Disabled"

    MinTranspositionTableSizeMB = 1
    MaxTranspositionTableSizeMB32Bit = 1024
    MaxTranspositionTableSizeMB64Bit = 2048

    MinMaxHelperThreads = 0
    MaxMaxHelperThreads = (multiprocessing.cpu_count() // 2) - 1

    MinMaxBranchingFactor = 1

    _max_helper_threads = None
    # Hard min is 0, hard max is (Environment.ProcessorCount / 2) - 1
    hard_max = min(_max_helper_threads, MaxMaxHelperThreads) if _max_helper_threads is not None else MaxMaxHelperThreads
    MaxHelperThreads = max(MinMaxHelperThreads, hard_max)

    MaxBranchingFactor = None
    ReportIntermediateBestMoves = False

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

        if root.text == "GameAI":
            self.load_game_ai_config([elem for elem in root])

    def load_game_ai_config(self, xml_tree):
        if xml_tree is None:
            raise ValueError("Invalid xml_tree.")

        for node in xml_tree:
            sub_elems = [sub_elem for sub_elem in node]

            if node.attrib == "TranspositionTableSizeMB":
                self.parse_transposition_table_size_mb_value(node.text)
            if node.attrib in ["MetricWeights", "StartMetricWeights"]:
                self.StartMetricWeights = MetricWeights().read_metric_weights_xml(sub_elems)
            if node.attrib == "EndMetricWeights":
                self.EndMetricWeights = MetricWeights().read_metric_weights_xml(sub_elems)
            if node.attrib == "MaxHelperThreads":
                self.parse_max_helper_threads_value(node.text)
            if node.attrib == "PonderDuringIdle":
                self.parse_ponder_during_idle_value(node.text)
            if node.attrib == "MaxBranchingFactor":
                self.parse_max_branching_factor_value(node.text)
            if node.attrib == "ReportIntermediateBestMoves":
                self.parse_report_intermediate_best_moves_value(sub_elems)

    def parse_transposition_table_size_mb_value(self, raw_value):
        int_value = int(raw_value)
        size = self.MaxTranspositionTableSizeMB64Bit if is_64 else self.MaxTranspositionTableSizeMB32Bit
        minimum = min(int_value, size)

        self.TranspositionTableSizeMB = max(self.MinTranspositionTableSizeMB, minimum)

    def get_transposition_table_size_mb_value(self):
        r_type = "int"

        default = TranspositionTable.DefaultSizeInBytes / (1024 * 1024)
        value = str(self.TranspositionTableSizeMB if self.TranspositionTableSizeMB is not None else default)

        size = self.MaxTranspositionTableSizeMB64Bit if is_64 else self.MaxTranspositionTableSizeMB32Bit
        values = "%d;%d" % (self.MinTranspositionTableSizeMB, size)
        return r_type, value, values

    def parse_max_helper_threads_value(self, raw_value):
        try:
            val = int(raw_value)
            self._max_helper_threads = max(self.MinMaxHelperThreads, min(val, self.MaxMaxHelperThreads))
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
        while i < self.MaxMaxHelperThreads:
            values += ";" + str(i)

        return r_type, value, values

    def parse_ponder_during_idle_value(self, raw_value):
        if raw_value in PonderDuringIdleTypes:
            self.PonderDuringIdle = raw_value

    def get_ponder_during_idle_value(self):
        r_type = "string"
        value = self.PonderDuringIdle
        values = "Disabled;SingleThreaded;MultiThreaded"
        return r_type, value, values

    def parse_max_branching_factor_value(self, raw_value):
        try:
            val = int(raw_value)
            self.MaxBranchingFactor = max(self.MinMaxBranchingFactor, min(val, GameAI.MaxMaxBranchingFactor))
        except ValueError:
            pass

    def get_max_branching_factor_value(self):
        r_type = "int"
        value = str(self.MaxBranchingFactor if self.MaxBranchingFactor is not None else GameAI.MaxMaxBranchingFactor)
        values = "%d;%d" % (self.MinMaxBranchingFactor, GameAI.MaxMaxBranchingFactor)
        return r_type, value, values

    def parse_report_intermediate_best_moves_value(self, raw_value):
        try:
            self.ReportIntermediateBestMoves = bool(raw_value)
        except ValueError:
            pass

    def get_report_intermediate_best_moves_value(self):
        r_type = "bool"
        value = str(self.ReportIntermediateBestMoves)
        values = ""
        return r_type, value, values

    def get_game_ai(self):
        return GameAI(GameAIConfig(
            self.StartMetricWeights,
            self.EndMetricWeights if self.EndMetricWeights else self.StartMetricWeights,
            self.MaxBranchingFactor,
            self.TranspositionTableSizeMB
        ))


def get_default_config():
    return GameEngineConfig(DefaultConfig)


MaxHelperThreadsTypes = ["Auto", "None"]
PonderDuringIdleTypes = ["Disabled", "SingleThreaded", "MultiThreaded"]

DefaultConfig = """
<?xml version="1.0" encoding="utf-8" ?>
<Mzinga.Engine>
<GameAI>
<TranspositionTableSizeMB>32</TranspositionTableSizeMB>
<MaxHelperThreads>Auto</MaxHelperThreads>
<PonderDuringIdle>SingleThreaded</PonderDuringIdle>
<ReportIntermediateBestMoves>False</ReportIntermediateBestMoves>
<StartMetricWeights>
<QueenBee.InPlayWeight>50837.031620256952</QueenBee.InPlayWeight>
<QueenBee.IsPinnedWeight>-35419.478140500571</QueenBee.IsPinnedWeight>
<QueenBee.IsCoveredWeight>-243.45622986720107</QueenBee.IsCoveredWeight>
<QueenBee.NoisyMoveWeight>-22355.989482597503</QueenBee.NoisyMoveWeight>
<QueenBee.QuietMoveWeight>-84105.741673420329</QueenBee.QuietMoveWeight>
<QueenBee.FriendlyNeighborWeight>-4947.40542859837</QueenBee.FriendlyNeighborWeight>
<QueenBee.EnemyNeighborWeight>-9121.7862907225845</QueenBee.EnemyNeighborWeight>
<Spider.InPlayWeight>-183922.24346427282</Spider.InPlayWeight>
<Spider.IsPinnedWeight>-51088.715966831391</Spider.IsPinnedWeight>
<Spider.IsCoveredWeight>206.990683117213</Spider.IsCoveredWeight>
<Spider.NoisyMoveWeight>94212.195816425025</Spider.NoisyMoveWeight>
<Spider.QuietMoveWeight>94605.450724741677</Spider.QuietMoveWeight>
<Spider.FriendlyNeighborWeight>-169652.09402653066</Spider.FriendlyNeighborWeight>
<Spider.EnemyNeighborWeight>-21579.439803066332</Spider.EnemyNeighborWeight>
<Beetle.InPlayWeight>-319624.73751234385</Beetle.InPlayWeight>
<Beetle.IsPinnedWeight>53938.865528570306</Beetle.IsPinnedWeight>
<Beetle.IsCoveredWeight>-337.4041303961796</Beetle.IsCoveredWeight>
<Beetle.NoisyMoveWeight>-485.60517579567255</Beetle.NoisyMoveWeight>
<Beetle.QuietMoveWeight>-106382.99553773669</Beetle.QuietMoveWeight>
<Beetle.FriendlyNeighborWeight>-356638.51686288341</Beetle.FriendlyNeighborWeight>
<Beetle.EnemyNeighborWeight>-8573.7450425364077</Beetle.EnemyNeighborWeight>
<Grasshopper.InPlayWeight>-27178.525364857123</Grasshopper.InPlayWeight>
<Grasshopper.IsPinnedWeight>-33404.490951421416</Grasshopper.IsPinnedWeight>
<Grasshopper.IsCoveredWeight>548.44065050905192</Grasshopper.IsCoveredWeight>
<Grasshopper.NoisyMoveWeight>77276.245224015787</Grasshopper.NoisyMoveWeight>
<Grasshopper.QuietMoveWeight>15766.311363153041</Grasshopper.QuietMoveWeight>
<Grasshopper.FriendlyNeighborWeight>-67886.490066017082</Grasshopper.FriendlyNeighborWeight>
<Grasshopper.EnemyNeighborWeight>14355.229523645041</Grasshopper.EnemyNeighborWeight>
<SoldierAnt.InPlayWeight>200139.2683608809</SoldierAnt.InPlayWeight>
<SoldierAnt.IsPinnedWeight>-62143.443626915083</SoldierAnt.IsPinnedWeight>
<SoldierAnt.IsCoveredWeight>-506.30530226706622</SoldierAnt.IsCoveredWeight>
<SoldierAnt.NoisyMoveWeight>9421.88332525417</SoldierAnt.NoisyMoveWeight>
<SoldierAnt.QuietMoveWeight>-2784.606961465232</SoldierAnt.QuietMoveWeight>
<SoldierAnt.FriendlyNeighborWeight>-13518.397319103129</SoldierAnt.FriendlyNeighborWeight>
<SoldierAnt.EnemyNeighborWeight>-56076.88001448063</SoldierAnt.EnemyNeighborWeight>
</StartMetricWeights>
<EndMetricWeights>
<QueenBee.InPlayWeight>17832.752038692164</QueenBee.InPlayWeight>
<QueenBee.IsPinnedWeight>-153259.6446560958</QueenBee.IsPinnedWeight>
<QueenBee.IsCoveredWeight>-12062.809088303911</QueenBee.IsCoveredWeight>
<QueenBee.NoisyMoveWeight>80822.665556267631</QueenBee.NoisyMoveWeight>
<QueenBee.QuietMoveWeight>134978.9720693233</QueenBee.QuietMoveWeight>
<QueenBee.FriendlyNeighborWeight>-381617.8635138495</QueenBee.FriendlyNeighborWeight>
<QueenBee.EnemyNeighborWeight>-521129.20243836124</QueenBee.EnemyNeighborWeight>
<Spider.InPlayWeight>-12791.45541050752</Spider.InPlayWeight>
<Spider.IsPinnedWeight>-61584.831349148</Spider.IsPinnedWeight>
<Spider.IsCoveredWeight>-775.35572307100165</Spider.IsCoveredWeight>
<Spider.NoisyMoveWeight>120090.56161788374</Spider.NoisyMoveWeight>
<Spider.QuietMoveWeight>-25620.550067509335</Spider.QuietMoveWeight>
<Spider.FriendlyNeighborWeight>50071.490767260431</Spider.FriendlyNeighborWeight>
<Spider.EnemyNeighborWeight>115729.74517664181</Spider.EnemyNeighborWeight>
<Beetle.InPlayWeight>-104764.43582698153</Beetle.InPlayWeight>
<Beetle.IsPinnedWeight>8148.1334677123405</Beetle.IsPinnedWeight>
<Beetle.IsCoveredWeight>-13504.915458214411</Beetle.IsCoveredWeight>
<Beetle.NoisyMoveWeight>75441.89545110683</Beetle.NoisyMoveWeight>
<Beetle.QuietMoveWeight>8154.507392742652</Beetle.QuietMoveWeight>
<Beetle.FriendlyNeighborWeight>2083.30649676445</Beetle.FriendlyNeighborWeight>
<Beetle.EnemyNeighborWeight>53817.23998276201</Beetle.EnemyNeighborWeight>
<Grasshopper.InPlayWeight>26486.8616248504</Grasshopper.InPlayWeight>
<Grasshopper.IsPinnedWeight>-81940.610176146263</Grasshopper.IsPinnedWeight>
<Grasshopper.IsCoveredWeight>5987.60021560749</Grasshopper.IsCoveredWeight>
<Grasshopper.NoisyMoveWeight>71575.748863625078</Grasshopper.NoisyMoveWeight>
<Grasshopper.QuietMoveWeight>-7989.0958909230549</Grasshopper.QuietMoveWeight>
<Grasshopper.FriendlyNeighborWeight>26619.553949671186</Grasshopper.FriendlyNeighborWeight>
<Grasshopper.EnemyNeighborWeight>80307.851786135026</Grasshopper.EnemyNeighborWeight>
<SoldierAnt.InPlayWeight>29983.953942488319</SoldierAnt.InPlayWeight>
<SoldierAnt.IsPinnedWeight>-50928.471194140635</SoldierAnt.IsPinnedWeight>
<SoldierAnt.IsCoveredWeight>-19457.846451490077</SoldierAnt.IsCoveredWeight>
<SoldierAnt.NoisyMoveWeight>25338.286810615977</SoldierAnt.NoisyMoveWeight>
<SoldierAnt.QuietMoveWeight>3628.0368716020935</SoldierAnt.QuietMoveWeight>
<SoldierAnt.FriendlyNeighborWeight>7118.0742514099165</SoldierAnt.FriendlyNeighborWeight>
<SoldierAnt.EnemyNeighborWeight>88105.512723272492</SoldierAnt.EnemyNeighborWeight>
</EndMetricWeights>
</GameAI>
</Mzinga.Engine>
"""
