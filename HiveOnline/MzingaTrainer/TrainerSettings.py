import datetime


class TrainerSettings:

    battle_shuffle_profiles = False
    lifecycle_battles = 1
    max_max_battles = -1
    max_max_concurrent_battles = -1
    game_type = "Original"  # "Original"
    mixed_game_types = False

    _battle_time_limit = datetime.timedelta(minutes=10)
    _bulk_battle_time_limit = datetime.timedelta(minutes=300)
    _max_draws = 1
    _max_battles = max_max_battles
    _max_concurrent_battles = max_max_concurrent_battles

    max_helper_threads = 0
    cull_min_keep_count = 2
    cull_keep_max = -1

    _profile_path = "/Users/tylergillson/Dropbox/UofC/F2018/CPSC.502.06/MzingaPorted/HiveOnline/MzingaTrainer/Profiles/"
    _white_profile_path = None
    _black_profile_path = None
    _target_profile_path = None

    provisional_rules = False
    provisional_game_count = 10

    mate_min_mix = 0.95
    mate_max_mix = 1.05
    mate_min_parent_count = 2
    mate_parent_max = -1
    mate_shuffle_parents = False
    _mate_parent_count = mate_parent_max

    trans_table_size = 32
    max_depth = -1

    _turn_max_time = None

    generate_min_weight = -100.0
    generate_max_weight = 100.0
    _generate_count = 1
    _cull_keep_count = cull_keep_max

    infinite_lifecycle_generations = -1
    _lifecycle_generations = 1

    @property
    def profile_path(self):
        return self._profile_path

    @profile_path.setter
    def profile_path(self, value):
        if not value or value.isspace():
            raise ValueError("Invalid profile_path")
        self._profile_path = value

    @property
    def white_profile_path(self):
        return self._white_profile_path

    @white_profile_path.setter
    def white_profile_path(self, value):
        if not value or value.isspace():
            raise ValueError("Invalid white_profile_path")
        self._white_profile_path = value

    @property
    def black_profile_path(self):
        return self._black_profile_path

    @black_profile_path.setter
    def black_profile_path(self, value):
        if not value or value.isspace():
            raise ValueError("Invalid black_profile_path")
        self._black_profile_path = value

    @property
    def cull_keep_count(self):
        return self._cull_keep_count

    @cull_keep_count.setter
    def cull_keep_count(self, value):
        if value < self.cull_min_keep_count and value != self.cull_keep_max:
            raise ValueError("Invalid cull_keep_count.")
        self._cull_keep_count = value

    @property
    def generate_count(self):
        return self._generate_count

    @generate_count.setter
    def generate_count(self, value):
        if value < 1:
            raise ValueError("Invalid generate_count.")
        self._generate_count = value

    @property
    def lifecycle_generations(self):
        return self._lifecycle_generations

    @lifecycle_generations.setter
    def lifecycle_generations(self, value):
        if value < 0:
            value = self.infinite_lifecycle_generations
        self._lifecycle_generations = value

    @property
    def max_draws(self):
        return self._max_draws

    @max_draws.setter
    def max_draws(self, value):
        if value < 1:
            raise ValueError("Invalid max_draws.")
        self._max_draws = value

    @property
    def max_battles(self):
        return self._max_battles

    @max_battles.setter
    def max_battles(self, value):
        if value < 1 and value != self.max_max_battles:
            raise ValueError("Invalid max_battles")
        self._max_battles = value

    @property
    def max_concurrent_battles(self):
        return self._max_concurrent_battles

    @max_concurrent_battles.setter
    def max_concurrent_battles(self, value):
        if value < 1 and value != self.max_max_concurrent_battles:
            raise ValueError("Invalid max_concurrent_battles")
        self._max_concurrent_battles = value

    @property
    def bulk_battle_time_limit(self):
        if self._bulk_battle_time_limit is None:
            self._bulk_battle_time_limit = datetime.timedelta.max
        return self._bulk_battle_time_limit

    @bulk_battle_time_limit.setter
    def bulk_battle_time_limit(self, value):
        self._bulk_battle_time_limit = datetime.timedelta(minutes=value)

    @property
    def mate_parent_count(self):
        return self._mate_parent_count

    @mate_parent_count.setter
    def mate_parent_count(self, value):
        if value < self.mate_min_parent_count and value != self.mate_parent_max:
            raise ValueError("Invalid mate_parent_count")
        self._mate_parent_count = value

    @property
    def battle_time_limit(self):
        if self._battle_time_limit is None:
            self._battle_time_limit = datetime.timedelta(minutes=25)
        return self._battle_time_limit

    @battle_time_limit.setter
    def battle_time_limit(self, value):
        self._battle_time_limit = datetime.timedelta(minutes=value)

    @property
    def target_profile_path(self):
        return self._target_profile_path

    @target_profile_path.setter
    def target_profile_path(self, value):
        if value is None or value.isspace():
            raise ValueError("Invalid target_profile_path")
        self._target_profile_path = value

    @property
    def turn_max_time(self):
        if self._turn_max_time is None:
            self._turn_max_time = datetime.timedelta(seconds=5)
        return self._turn_max_time

    @turn_max_time.setter
    def turn_max_time(self, value):
        self._turn_max_time = datetime.timedelta(seconds=value)
