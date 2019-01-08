class GameAIConfig:
    def __init__(self, start_weights, end_weights, t_table_size, game_type, b_factor=None, board_weights=None):
        self.BoardMetricWeights = board_weights
        self.StartMetricWeights = start_weights
        self.EndMetricWeights = end_weights
        self.TranspositionTableSizeMB = t_table_size
        self.GameType = game_type
        self.MaxBranchingFactor = b_factor
