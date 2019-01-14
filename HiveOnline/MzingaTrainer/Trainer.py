import asyncio
import cProfile
import datetime
import random
import math
import queue
import threading
import os
from typing import List
from functools import reduce

from MzingaShared.Core.GameBoard import GameBoard
from MzingaShared.Core.AI.BoardMetricWeights import BoardMetricWeights as BoardMetricWeightsCls
from MzingaShared.Core.AI.MetricWeights import MetricWeights as MetricWeightsCls
from MzingaShared.Core.AI.GameAI import GameAI
from MzingaShared.Core.AI.GameAIConfig import GameAIConfig
from MzingaTrainer.Profile import Profile
from MzingaTrainer import EloUtils
from MzingaTrainer.EloUtils import EloUtils as EloUtilsCls
from MzingaTrainer.TrainerSettings import TrainerSettings

GameResults = ["Loss", "Draw", "Win"]

run_profile = False


class Trainer:
    _start_time = None
    _settings = None
    _random = None
    _elo_lock = threading.Lock()
    _progress_lock = threading.Lock()
    _white_profile_lock = threading.Lock()
    _black_profile_lock = threading.Lock()

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        if self._start_time is None:
            self._start_time = value

    @property
    def trainer_settings(self):
        return self._settings

    @trainer_settings.setter
    def trainer_settings(self, value):
        if value is None:
            raise ValueError("Invalid trainer_settings.")
        self._settings = value

    @property
    def random(self):
        if self._random:
            return self._random
        self._random = random.Random()
        return self._random

    def __init__(self):
        self.trainer_settings = TrainerSettings()
        self.board_metric_weights_cls = BoardMetricWeightsCls()
        self.metric_weights_cls = MetricWeightsCls(self._settings.GameType)
        self.start_time = None

    def battle(self, white_profile_path=None, black_profile_path=None):
        if white_profile_path is None and black_profile_path is None:
            return self.battle(self.trainer_settings.white_profile_path, self.trainer_settings.black_profile_path)

        if white_profile_path.isspace():
            raise ValueError("Invalid white_profile_path.")
        if black_profile_path.isspace():
            raise ValueError("Invalid black_profile_path.")

        self.start_time = datetime.datetime.now()

        # Load, then battle profiles:
        white_profile = self.read_profile(white_profile_path)
        black_profile = self.read_profile(black_profile_path)
        self.battle_profiles(white_profile, black_profile)

        # Save Profiles
        self.write_profile(white_profile_path, white_profile)
        self.write_profile(black_profile_path, black_profile)

    def battle_royale(self, *args):
        if len(args) == 0:
            args = [self.trainer_settings.profile_path, self.trainer_settings.max_battles,
                    self.trainer_settings.max_draws, self.trainer_settings.bulk_battle_time_limit,
                    self.trainer_settings.BattleShuffleProfiles, self.trainer_settings.max_concurrent_battles]
            return self.battle_royale(*args)
        else:
            path, max_battles, max_draws, time_limit, shuffle_profiles, max_concurrent_battles = args

            if path.isspace():
                raise ValueError("Invalid path.")
            if max_battles < 1 and max_battles != self.trainer_settings.MaxMaxBattles:
                raise ValueError("Invalid max_battles.")
            if max_draws < 1:
                raise ValueError("Invalid max_draws.")
            if max_concurrent_battles < 1 and max_concurrent_battles != self.trainer_settings.max_concurrent_battles:
                raise ValueError("Invalid max_concurrent_battles.")

        self.start_time = datetime.datetime.now()
        br_start = datetime.datetime.now()

        profile_list = self.load_profiles(path)
        combinations = len(profile_list) * (len(profile_list) - 1)

        if max_battles == self.trainer_settings.MaxMaxBattles:
            max_battles = combinations
        max_battles = min(max_battles, combinations)

        total = max_battles
        completed = 0
        remaining = total

        time_remaining = datetime.timedelta(seconds=self.trainer_settings.battle_time_limit.seconds * total)
        timeout_remaining = time_limit - (datetime.datetime.now() - br_start)
        ts = self.to_string
        eta = ts(timeout_remaining) if timeout_remaining < time_remaining else ts(time_remaining)
        self.log("Battle Royale start, ETA: %s." % eta)

        white_profiles = list(sorted(profile_list, key=lambda x: x.EloRating))
        black_profiles = list(sorted(profile_list, key=lambda x: x.EloRating, reverse=True))
        matches = list(set((wp, bp) for wp in white_profiles for bp in black_profiles if wp != bp))

        if shuffle_profiles:
            matches = self.shuffle(matches)

        for match in matches:
            w_profile = match[0]
            b_profile = match[1]
            round_result = "Draw"

            w_s, b_s = ts(w_profile), ts(b_profile)
            self.log("Battle Royale match start %s vs. %s." % (w_s, b_s))

            if max_draws == 1:
                _ = self.battle_profiles(w_profile, b_profile)
            else:
                rounds = 0
                while round_result == "Draw":
                    self.log("Battle Royale round %d start." % rounds + 1)

                    round_result = self.battle_profiles(w_profile, b_profile)

                    self.log("Battle Royale round %d end." % rounds + 1)

                    rounds += 1

                    if rounds >= max_draws and round_result == "Draw":
                        self.log("Battle Royale match draw-out.")
                        break

            w_s, b_s = ts(w_profile), ts(b_profile)
            self.log("Battle Royale match end %s vs. %s." % (w_s, b_s))

            with self._progress_lock:
                completed += 1
                remaining -= 1

            # Save Profiles
            with self._white_profile_lock:
                w_profile_path = "".join([path, str(w_profile.Id), ".xml"])
                self.write_profile(w_profile_path, w_profile)

            with self._black_profile_lock:
                b_profile_path = "".join([path, str(b_profile.Id), ".xml"])
                self.write_profile(b_profile_path, b_profile)

            with self._progress_lock:
                timeout_remaining = time_limit - (datetime.datetime.now() - br_start)
                progress, time_remaining = self.get_progress(br_start, completed, remaining)

                eta = ts(timeout_remaining) if timeout_remaining < time_remaining else ts(time_remaining)
                self.log("Battle Royale progress: %6.2f, ETA: %s." % (progress, eta))

            if timeout_remaining <= datetime.timedelta.min:
                break

        if time_limit - (datetime.datetime.now() - br_start) <= datetime.timedelta.min:
            self.log("Battle Royale time-out.")

        self.log("Battle Royale end, elapsed time: %s." % ts(datetime.datetime.now() - br_start))

        best = list(sorted(profile_list, key=lambda x: x.EloRating))[0]

        self.log("Battle Royale Highest Elo: %s" % ts(best))

    def battle_profiles(self, white_profile, black_profile):
        if white_profile is None:
            raise ValueError("Invalid white_profile.")
        if black_profile is None:
            raise ValueError("Invalid black_profile.")
        if white_profile.Id == black_profile.Id:
            raise ValueError("Profile cannot battle itself.")

        # Create Game
        game_board = GameBoard(board_string="START", game_type=self.trainer_settings.GameType)

        # Create AIs
        white_ai = GameAI(GameAIConfig(
            white_profile.StartMetricWeights,
            white_profile.EndMetricWeights,
            self.trainer_settings.TransTableSize,
            self._settings.GameType,
            board_weights=white_profile.BoardMetricWeights)
        )
        black_ai = GameAI(GameAIConfig(
            black_profile.StartMetricWeights,
            black_profile.EndMetricWeights,
            self.trainer_settings.TransTableSize,
            self._settings.GameType,
            board_weights=black_profile.BoardMetricWeights)
        )
        time_limit = self.trainer_settings.battle_time_limit

        w_s, b_s = self.to_string(white_profile), self.to_string(black_profile)
        self.log("Battle start %s vs. %s." % (w_s, b_s))

        battle_start = datetime.datetime.now()
        board_keys = []

        try:
            while game_board.game_in_progress:  # Play Game
                board_keys.append(game_board.zobrist_key)

                if len(board_keys) >= 6:
                    last_index = len(board_keys) - 1
                    a = board_keys[last_index] == board_keys[last_index - 2] == board_keys[last_index - 4]
                    b = board_keys[last_index - 1] == board_keys[last_index - 3] == board_keys[last_index - 5]
                    if a or b:
                        self.log("Battle loop-out.")
                        break

                battle_elapsed = datetime.datetime.now() - battle_start
                if battle_elapsed > time_limit:
                    self.log("Battle time-out.")
                    break

                ai = white_ai if game_board.current_turn_colour == "White" else black_ai

                ############################################################
                if run_profile:
                    pr = cProfile.Profile()
                    pr.enable()
                    move = self.get_best_move(game_board, ai)
                    pr.disable()
                    pr.dump_stats('/Users/tylergillson/Desktop/output.prof')
                ############################################################
                else:
                    move = self.get_best_move(game_board, ai)
                game_board.play(move[0])

        except Exception as ex:
            self.log("Battle interrupted with exception: %s" % ex)

        board_state = "Draw" if game_board.game_in_progress else game_board.BoardState

        # Load Results
        white_score = 0.0
        black_score = 0.0
        white_result = "Loss"
        black_result = "Loss"

        if board_state == "WhiteWins":
            white_score, black_score, white_result = (1.0, 0.0, "Win")
        if board_state == "BlackWins":
            white_score, black_score, black_result = (0.0, 1.0, "Win")
        if board_state == "Draw":
            white_score, black_score, white_result, black_result = (0.5, 0.5, "Draw", "Draw")

        with self._white_profile_lock:
            white_rating = white_profile.EloRating
            white_k = EloUtils.ProvisionalK if self.is_provisional(white_profile) else EloUtils.DefaultK

        with self._black_profile_lock:
            black_rating = black_profile.EloRating
            black_k = EloUtils.ProvisionalK if self.is_provisional(black_profile) else EloUtils.DefaultK

        with self._elo_lock:
            white_end_rating, black_end_rating = EloUtilsCls.update_ratings(
                white_rating, black_rating, white_score, black_score, white_k, black_k)

        with self._white_profile_lock:
            white_profile.update_record(white_end_rating, white_result)

        with self._black_profile_lock:
            black_profile.update_record(black_end_rating, black_result)

        # Output Results
        w_s, b_s = self.to_string(white_profile), self.to_string(black_profile)
        self.log("Battle end %s %s vs. %s" % (board_state, w_s, b_s))

        return board_state

    def get_best_move(self, game_board, ai):
        game_board.GameType = ai.GameType

        if self.trainer_settings.MaxDepth >= 0:
            future = asyncio.ensure_future(
                ai.get_best_move(
                    game_board,
                    max_depth=self.trainer_settings.MaxDepth,
                    max_helper_threads=self.trainer_settings.MaxHelperThreads))
        else:
            future = asyncio.ensure_future(
                ai.get_best_move(
                    game_board,
                    max_time=self.trainer_settings.TurnMaxTime,
                    max_helper_threads=self.trainer_settings.MaxHelperThreads))

        loop = asyncio.get_event_loop()
        done, _ = loop.run_until_complete(asyncio.wait([future]))
        results = [fut.result() for fut in done]
        return results

    def cull(self, path=None, keep_count=None, provisional_rules=None):
        if path is None:
            return self.cull(self.trainer_settings.profile_path,
                             self.trainer_settings.cull_keep_count,
                             self.trainer_settings.ProvisionalRules)
        else:
            if path.isspace():
                raise ValueError("Invalid path.")
            if keep_count < self.trainer_settings.CullMinKeepCount and keep_count != self.trainer_settings.CullKeepMax:
                raise ValueError("Invalid keep_count.")

            self.start_time = datetime.datetime.now()
            self.log("Cull start.")

            profile_list = self.load_profiles(path)

            if provisional_rules:
                profile_list = [p for p in profile_list if not self.is_provisional(p)]

            profile_list = list(sorted(profile_list, key=lambda x: x.EloRating))

            if keep_count == self.trainer_settings.CullKeepMax:
                keep_count = max(self.trainer_settings.CullMinKeepCount, round(math.sqrt(len(profile_list))))

            if not os.path.exists(path + "Culled"):
                os.mkdir(path + "Culled")

            count = 0
            for p in profile_list:
                if count < keep_count:
                    self.log("Kept %s." % self.to_string(p))
                    count += 1
                else:
                    source_file = "".join([path, str(p.Id), ".xml"])
                    dest_file = "".join([path, "Culled/", str(p.Id), ".xml"])

                    os.rename(source_file, dest_file)
                    self.log("Culled %s." % self.to_string(p))

            self.log("Cull end.")

    def enumerate(self, path=None):
        if path is None:
            return self.enumerate(self.trainer_settings.profile_path)
        else:
            if path.isspace():
                raise ValueError("Invalid path.")

            self.start_time = datetime.datetime.now()
            self.log("Enumerate start.")

            profile_list = self.load_profiles(path)
            profile_list = list(sorted(profile_list, key=lambda x: x.EloRating))

            for p in profile_list:
                self.log("%s" % self.to_string(p))

            self.log("Enumerate end.")

    def load_profiles(self, path) -> List[Profile]:
        if path.isspace():
            raise ValueError("Invalid path.")

        files = [f for f in os.listdir(path) if f.endswith(".xml")]
        return [self.read_profile(path + f) for f in files]

    def log(self, output):
        elapsed_time = datetime.datetime.now() - self.start_time
        print("%s > %s" % (self.to_string(elapsed_time), output))

    def analyze(self, path=None):
        if path is None:
            return self.analyze(self.trainer_settings.profile_path)
        else:
            if path.isspace():
                raise ValueError("Invalid path.")

            self.start_time = datetime.datetime.now()
            self.log("Analyze start.")

            profile_list: List[Profile] = self.load_profiles(path)
            profile_list = list(sorted(profile_list, key=lambda x: x.EloRating))

            result_file = path + "analyze.csv"
            with open(result_file, "w") as f:
                header = "Id,Name,GameType,EloRating,Generation,ParentA,ParentB,Wins,Losses,Draws"

                def add_csv_weights(bug_type, bug_type_weight):
                    return "".join([",Start%s.%s" % (bug_type, bug_type_weight),
                                    ",End%s.%s" % (bug_type, bug_type_weight)])

                data_strs = self.metric_weights_cls.iterate_over_weights_result(add_csv_weights, [])
                header += reduce((lambda a, b: a + b), data_strs)
                f.write(header)
                f.write("\n")

                def add_csv_norm_weights(bug_type, bug_type_weight, **kwargs):
                    start_normalized = kwargs.pop('start_normalized')
                    end_normalized = kwargs.pop('end_normalized')
                    return "".join([",%6.2f" % float(start_normalized.get(bug_type, bug_type_weight)),
                                    ",%6.2f" % float(end_normalized.get(bug_type, bug_type_weight))])

                for p in profile_list:
                    profile_str = "%s,%s,%s,%d,%d,%s,%s,%d,%d,%d" % (p.Id, p.Name, p.GameType,
                                                                     p.EloRating, p.Generation,
                                                                     p.ParentA if p.ParentA is not None else "",
                                                                     p.ParentB if p.ParentB is not None else "",
                                                                     p.Wins, p.Losses, p.Draws)

                    sn = p.StartMetricWeights.get_normalized()
                    en = p.EndMetricWeights.get_normalized()
                    data_strs = self.metric_weights_cls.iterate_over_weights_result(
                        add_csv_norm_weights, [], start_normalized=sn, end_normalized=en)

                    profile_str += reduce((lambda a, b: a + b), data_strs)
                    f.write(profile_str)
                    f.write("\n")

            self.log("Analyze end.")

    def generate(self, path=None, count=None, game_type=None, min_weight=None, max_weight=None):
        if path is None:
            return self.generate(self.trainer_settings.profile_path,
                                 self.trainer_settings.generate_count,
                                 self.trainer_settings.GameType,
                                 self.trainer_settings.GenerateMinWeight,
                                 self.trainer_settings.GenerateMaxWeight)
        else:
            if path.isspace():
                raise ValueError("Invalid path.")
            if count < 1:
                raise ValueError("Invalid count.")

            self.start_time = datetime.datetime.now()
            self.log("Generate start.")

            if not os.path.exists(path):
                os.mkdir(path)

            for i in range(count):
                profile = Profile.generate(min_weight, max_weight, game_type)
                file_path = "".join([path, str(profile.Id), ".xml"])
                self.write_profile(file_path, profile)
                self.log("Generated %s." % self.to_string(profile))

            self.log("Generate end.")

    def lifecycle(self, path=None, generations=None, battles=None):
        if path is None:
            return self.lifecycle(self.trainer_settings.profile_path,
                                  self.trainer_settings.lifecycle_generations,
                                  self.trainer_settings.LifecycleBattles)
        else:
            if path.isspace():
                raise ValueError("Invalid path.")
            if generations == 0:
                raise ValueError("Invalid generations.")

        self.start_time = datetime.datetime.now()
        lifecycle_start = datetime.datetime.now()
        self.log("Lifecycle start.")

        gen = 1
        while generations == self.trainer_settings.InfiniteLifeCycleGenerations or gen <= generations:
            if generations != 1:
                self.log("Lifecycle generation %d start." % gen)

            # Battle
            if battles != 0:
                for j in range(abs(battles)):
                    if battles < 0:
                        self.tournament(path, self.trainer_settings.max_draws,
                                        self.trainer_settings.bulk_battle_time_limit,
                                        self.trainer_settings.BattleShuffleProfiles,
                                        self.trainer_settings.max_concurrent_battles)
                    elif battles > 0:
                        args = [path, self.trainer_settings.max_battles, self.trainer_settings.max_draws,
                                self.trainer_settings.bulk_battle_time_limit,
                                self.trainer_settings.BattleShuffleProfiles,
                                self.trainer_settings.max_concurrent_battles]
                        self.battle_royale(args)

            # Cull & Mate
            self.cull(path, self.trainer_settings.cull_keep_count, self.trainer_settings.ProvisionalRules)
            self.mate(path)

            if generations != 1:
                self.log("Lifecycle generation %d end." % gen)

            if generations > 0:
                progress, time_remaining = self.get_progress(lifecycle_start, gen, generations - gen)
                self.log("Lifecycle progress: %6.2f ETA %s." % (progress, self.to_string(time_remaining)))

            # Output analysis
            self.analyze(path)
            gen += 1

        self.log("Lifecycle end.")

    def mate(self, path=None, *args):
        if path is None:
            return self.mate(self.trainer_settings.profile_path)
        elif len(args) == 0:
            args = [self.trainer_settings.MateMinMix, self.trainer_settings.MateMaxMix,
                    self.trainer_settings.mate_parent_count, self.trainer_settings.MateShuffleParents,
                    self.trainer_settings.ProvisionalRules]
            return self.mate(path, *args)
        else:
            if path.isspace():
                raise ValueError("Invalid path.")

            min_mix, max_mix, parent_count, shuffle_parents, provisional_rules = args

            if min_mix > max_mix:
                raise ValueError("Invalid min_mix.")

            too_few = parent_count < self.trainer_settings.MateMinParentCount
            if too_few and parent_count != self.trainer_settings.MateParentMax:
                raise ValueError("Invalid parent_count.")

            self.start_time = datetime.datetime.now()
            self.log("Mate start.")

            profiles_list = self.load_profiles(path)

            if provisional_rules:
                profiles_list = [p for p in profiles_list if not self.is_provisional(p)]

            profiles_list = self.shuffle(profiles_list) if shuffle_parents else self.seed(profiles_list)

            max_parents = len(profiles_list) - (len(profiles_list) % 2)
            if parent_count == self.trainer_settings.MateParentMax:
                parent_count = max_parents

            parent_count = min(parent_count, max_parents)  # No more parents that exist

            if parent_count >= self.trainer_settings.MateMinParentCount:
                parents = queue.Queue()
                for i, p in enumerate(profiles_list):
                    if i == parent_count:
                        break
                    parents.put(profiles_list[i])

                while parents.qsize() >= 2:
                    parent_a = parents.get()
                    parent_b = parents.get()
                    child = Profile.mate(parent_a, parent_b, min_mix, max_mix)

                    pa, pb, ch = self.to_string(parent_a), self.to_string(parent_b), self.to_string(child)
                    self.log("Mated %s and %s to sire %s." % (pa, pb, ch))

                    file_path = "".join([path, str(child.Id), ".xml"])
                    self.write_profile(file_path, child)

            self.log("Mate end.")

    def tournament(self, *args):
        if len(args) == 0:
            args = [self.trainer_settings.profile_path, self.trainer_settings.max_draws,
                    self.trainer_settings.bulk_battle_time_limit, self.trainer_settings.BattleShuffleProfiles,
                    self.trainer_settings.max_concurrent_battles]
            return self.tournament(*args)
        else:
            path, max_draws, time_limit, shuffle_profiles, max_concurrent_battles = args

            if path.isspace():
                raise ValueError("Invalid path.")
            if max_draws < 1:
                raise ValueError("Invalid max_draws.")
            if max_concurrent_battles < 1 and max_concurrent_battles != self.trainer_settings.MaxMaxConcurrentBattles:
                raise ValueError("Invalid max_concurrent_battles.")

            self.start_time = datetime.datetime.now()
            tournament_start = datetime.datetime.now()

            profiles = self.load_profiles(path)
            total = len(profiles) - 1
            completed = 0
            remaining = total

            time_remaining = datetime.timedelta(seconds=self.trainer_settings.battle_time_limit.seconds * total)
            timeout_remaining = time_limit - (datetime.datetime.now() - tournament_start)
            ts = self.to_string

            s = ts(timeout_remaining) if timeout_remaining < time_remaining else ts(time_remaining)
            self.log("Tournament start, ETA: %s." % s)

            current_tier = self.shuffle(profiles) if shuffle_profiles else self.seed(profiles)
            tier = 1

            while len(current_tier) > 1:
                self.log("Tournament tier %d start, %d participants." % (tier, len(current_tier)))

                winners = []
                for i in range(len(current_tier) // 2):
                    profile_index = i * 2

                    if profile_index == len(current_tier) - 1:
                        # Odd profile out, gimme
                        self.log("Tournament auto-advances %s." % ts(current_tier[profile_index]))
                        winners.append(current_tier[profile_index])
                    else:
                        white_index = self.random.randrange(0, 2)  # Help mitigate top players always playing white
                        white_profile = current_tier[profile_index + white_index]
                        black_profile = current_tier[profile_index + 1 - white_index]

                        round_result = "Draw"

                        white_higher_rank = white_profile.EloRating < black_profile.EloRating
                        draw_winner_profile = white_profile if white_higher_rank else black_profile

                        w_s, b_s = ts(white_profile), ts(black_profile)
                        self.log("Tournament match start %s vs. %s." % (w_s, b_s))

                        if max_draws == 1:
                            round_result = self.battle_profiles(white_profile, black_profile)
                        else:
                            rounds = 0
                            while round_result == "Draw":
                                self.log("Tournament round %d start." % (rounds + 1))
                                round_result = self.battle_profiles(white_profile, black_profile)

                                self.log("Tournament round %d end." % (rounds + 1))
                                rounds += 1

                                if rounds >= max_draws and round_result == "Draw":
                                    self.log("Tournament match draw-out.")
                                    break

                        if round_result == "Draw":
                            round_result = "WhiteWins" if draw_winner_profile == white_profile else "BlackWins"

                        w_s, b_s = ts(white_profile), ts(black_profile)
                        self.log("Tournament match end %s vs. %s." % (w_s, b_s))

                        with self._progress_lock:
                            completed += 1
                            remaining -= 1

                        # Add winner back into the participant queue
                        if round_result == "WhiteWins":
                            winners.append(white_profile)
                        elif round_result == "BlackWins":
                            winners.append(black_profile)

                        self.log("Tournament advances %s." % ts(winners[i]))

                        # Save Profiles
                        with self._white_profile_lock:
                            white_profile_path = "".join([path, str(white_profile.Id), ".xml"])
                            self.write_profile(white_profile_path, white_profile)

                        with self._black_profile_lock:
                            black_profile_path = "".join([path, str(black_profile.Id), ".xml"])
                            self.write_profile(black_profile_path, black_profile)

                        with self._progress_lock:
                            timeout_remaining = time_limit - (datetime.datetime.now() - tournament_start)

                            progress, time_remaining = self.get_progress(tournament_start, completed, remaining)
                            eta = ts(timeout_remaining) if timeout_remaining < time_remaining else ts(time_remaining)
                            self.log("Tournament progress: %6.2f, ETA: %s." % (progress, eta))

                        if timeout_remaining <= datetime.timedelta.min:
                            break

                self.log("Tournament tier %d end." % tier)
                tier += 1

                current_tier = winners

                if time_limit - (datetime.datetime.now() - tournament_start) <= datetime.timedelta.min:
                    self.log("Tournament time-out.")
                    break

            self.log("Tournament end, elapsed time: %s." % ts(datetime.datetime.now() - tournament_start))

            if len(current_tier) == 1 and current_tier[0] is not None:
                winner = current_tier[0]
                self.log("Tournament Winner: %s" % ts(winner))

            best = list(sorted(profiles, key=lambda x: x.EloRating))[0]
            self.log("Tournament Highest Elo: %s" % ts(best))

    def to_string(self, val):
        if isinstance(val, datetime.timedelta):
            return "%d.%d:%d:%d" % (val.days, val.seconds // 3600, val.seconds // 60, val.seconds)
        elif isinstance(val, Profile):
            if val is None:
                raise ValueError("Invalid profile.")

            prov = "?" if self.is_provisional(val) else ""
            return "%s(%d%s %d/%d/%d)" % (val.Name, val.EloRating, prov, val.Wins, val.Losses, val.Draws)

    def is_provisional(self, profile):
        if profile is None:
            raise ValueError("Invalid profile.")
        return profile.total_games < self.trainer_settings.ProvisionalGameCount

    def shuffle(self, items):
        if items is None:
            raise ValueError("Invalid items.")

        shuffled = []
        while len(items) > 0:
            rand_index = self.random.randrange(len(items))
            shuffled.append(items.pop(rand_index))

        return shuffled

    @staticmethod
    def read_profile(file_path):
        with open(file_path, "r") as f:
            return Profile.read_xml(f)

    @staticmethod
    def write_profile(file_path, profile):
        with open(file_path, "wb+") as f:
            profile.write_xml(f)

    @staticmethod
    def seed(profile_list):
        if profile_list is None:
            raise ValueError("Invalid profiles_list")

        sorted_profiles = list(sorted(profile_list, key=lambda x: x.EloRating))
        seeded = []
        first = True

        while len(sorted_profiles) > 0:
            if first:
                seeded.append(sorted_profiles.pop(0))
            else:
                seeded.append(sorted_profiles.pop(-1))
            first = not first

        return seeded

    @staticmethod
    def get_progress(start_time, completed, remaining):
        if completed < 0:
            raise ValueError("Invalid completed.")
        if remaining < 0:
            raise ValueError("Invalid remaining.")

        total = completed + remaining

        if completed == 0:
            progress = 0.0
            time_remaining = datetime.timedelta.max
        elif remaining == 0:
            progress = 1.0
            time_remaining = datetime.timedelta.min
        else:
            elapsed_time = datetime.datetime.now() - start_time
            elapsed_ms = elapsed_time.seconds / 1000
            avg_ms = elapsed_ms / completed

            progress = completed / total
            time_remaining = datetime.timedelta(milliseconds=avg_ms * remaining)

        return progress, time_remaining
