class GameAIConfig(object):
    __slots__ = "start_metric_weights", "end_metric_weights", \
                "transposition_table_size_mb", "game_type", \
                "max_branching_factor", "board_metric_weights", "use_heuristics"

    def __init__(self, start_weights, end_weights, t_table_size, game_type, **kwargs):
        self.start_metric_weights = start_weights
        self.end_metric_weights = end_weights
        self.transposition_table_size_mb = t_table_size
        self.game_type = game_type
        self.max_branching_factor = kwargs.pop('b_factor', None)
        self.board_metric_weights = kwargs.pop('board_weights', None)
        self.use_heuristics = kwargs.pop('use_heuristics', None)
