import datetime


class TrainerSettings:

    BattleShuffleProfiles = False
    LifecycleBattles = 1
    MaxMaxBattles = -1
    MaxMaxConcurrentBattles = -1

    _battleTimeLimit = datetime.timedelta(minutes=5)
    _bulkBattleTimeLimit = datetime.timedelta(minutes=60)
    _maxDraws = 1
    _maxBattles = MaxMaxBattles
    _maxConcurrentBattles = MaxMaxConcurrentBattles

    MaxHelperThreads = 0
    CullMinKeepCount = 2
    CullKeepMax = -1

    _profiles_path = "/Users/tylergillson/Dropbox/UofC/F2018/CPSC.502.06/MzingaPorted/MzingaTrainer/Profiles/"
    _white_profile_path = "/Users/tylergillson/Dropbox/UofC/F2018/CPSC.502.06/MzingaPorted/MzingaTrainer/Profiles/WhiteProfiles/"
    _black_profile_path = "/Users/tylergillson/Dropbox/UofC/F2018/CPSC.502.06/MzingaPorted/MzingaTrainer/Profiles/BlackProfiles/"
    _target_profile_path = None

    ProvisionalRules = True
    ProvisionalGameCount = 30

    MateMinMix = 0.95
    MateMaxMix = 1.05
    MateMinParentCount = 2
    MateParentMax = -1
    MateShuffleParents = False
    _mateParentCount = MateParentMax

    TransTableSize = 32
    MaxDepth = -1

    TurnMaxTime = datetime.timedelta(seconds=5.0)

    GenerateMinWeight = -100.0
    GenerateMaxWeight = 100.0
    _generate_count = 1
    _cull_keep_count = CullKeepMax

    InfiniteLifeCycleGenerations = -1
    _lifecycleGenerations = 1

    @property
    def profiles_path(self):
        return self._profiles_path

    @profiles_path.setter
    def profiles_path(self, value):
        if not value or value.isspace():
            raise ValueError("Invalid profiles_path")
        self._profiles_path = value

    @property
    def white_profiles_path(self):
        return self._white_profile_path

    @white_profiles_path.setter
    def white_profiles_path(self, value):
        if not value or value.isspace():
            raise ValueError("Invalid white_profile_path")
        self._white_profile_path = value

    @property
    def black_profiles_path(self):
        return self._black_profile_path

    @black_profiles_path.setter
    def black_profiles_path(self, value):
        if not value or value.isspace():
            raise ValueError("Invalid black_profile_path")
        self._black_profile_path = value

    @property
    def cull_keep_count(self):
        return self._cull_keep_count

    @cull_keep_count.setter
    def cull_keep_count(self, value):
        if value < self.CullMinKeepCount and value != self.CullKeepMax:
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
        return self._lifecycleGenerations

    @lifecycle_generations.setter
    def lifecycle_generations(self, value):
        if value < 0:
            value = self.InfiniteLifeCycleGenerations
        self._lifecycleGenerations = value

    @property
    def max_draws(self):
        return self._maxDraws

    @max_draws.setter
    def max_draws(self, value):
        if value < 1:
            raise ValueError("Invalid max_draws.")
        self._maxDraws = value

    @property
    def max_battles(self):
        return self._maxBattles

    @max_battles.setter
    def max_battles(self, value):
        if value < 1 and value != self.MaxMaxBattles:
            raise ValueError("Invalid max_battles")
        self._maxBattles = value

    @property
    def max_concurrent_battles(self):
        return self._maxConcurrentBattles

    @max_concurrent_battles.setter
    def max_concurrent_battles(self, value):
        if value < 1 and value != self.MaxMaxConcurrentBattles:
            raise ValueError("Invalid max_concurrent_battles")
        self._maxConcurrentBattles = value

    @property
    def bulk_battle_time_limit(self):
        if self._bulkBattleTimeLimit is None:
            self._bulkBattleTimeLimit = datetime.timedelta.max
        return self._bulkBattleTimeLimit

    @bulk_battle_time_limit.setter
    def bulk_battle_time_limit(self, value):
        self._bulkBattleTimeLimit = value

    @property
    def mate_parent_count(self):
        return self._mateParentCount

    @mate_parent_count.setter
    def mate_parent_count(self, value):
        if value < self.MateMinParentCount and value != self.MateParentMax:
            raise ValueError("Invalid mate_parent_count")
        self._mateParentCount = value

    @property
    def battle_time_limit(self):
        if self._battleTimeLimit is None:
            self._battleTimeLimit = datetime.timedelta(minutes=5)
        return self._battleTimeLimit

    @battle_time_limit.setter
    def battle_time_limit(self, value):
        self._battleTimeLimit = value

    @property
    def target_profile_path(self):
        return self._target_profile_path

    @target_profile_path.setter
    def target_profile_path(self, value):
        if value is None or value.isspace():
            raise ValueError("Invalid target_profile_path")
        self._target_profile_path = value
