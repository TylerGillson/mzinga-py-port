class GameAIConfig:
    def __init__(self, start_weights, end_weights, t_table_size, b_factor=None):
        self.StartMetricWeights = start_weights
        self.EndMetricWeights = end_weights

        self.MaxBranchingFactor = b_factor
        self.TranspositionTableSizeMB = t_table_size
