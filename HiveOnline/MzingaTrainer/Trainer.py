import datetime
import math
import queue
import os
import multiprocessing as mp
from typing import List
from functools import reduce

from MzingaTrainer.Profile import Profile
from MzingaTrainer.TrainerBase import TrainerBase
from MzingaTrainer.TrainerCounter import TrainerCounter

trainer_counter = None


def work_tournament(*args):
    return args[0][0].simulate_tier_battle(*args[0][1:])


def work_battle_royale(*args):
    return args[0][0].simulate_match(*args[0][1:])


class Trainer(TrainerBase):

    def __init__(self):
        super().__init__()
        self.start_time = None

    def analyze(self, path=None):
        if path is None:
            return self.analyze(self.trainer_settings.profile_path)
        else:
            if path.isspace():
                raise ValueError("Invalid path.")

            self.start_time = datetime.datetime.now()
            self.log("Analyze start.")

            profile_list: List[Profile] = self.load_profiles(path)
            profile_list = list(sorted(profile_list, key=lambda x: x.elo_rating))

            result_file = path + "analyze.csv"
            with open(result_file, "w") as f:
                header = "id,name,game_type,elo_rating,generation,parent_a,parent_b,wins,losses,draws"

                def add_csv_weights(bug_type, bug_type_weight):
                    return "".join([",Start%s.%s" % (bug_type, bug_type_weight),
                                    ",End%s.%s" % (bug_type, bug_type_weight)])

                if profile_list[0].game_type == "Extended":
                    header += ",queen_bee_life_weight,queen_bee_tight_spaces_weight,noisy_ring_weight"

                data_strs = self.metric_weights_cls.iterate_over_weights_result(add_csv_weights, [])
                header += reduce((lambda a, b: a + b), data_strs)
                f.write(header)
                f.write("\n")

                def add_csv_norm_weights(bug_type, bug_type_weight, **kwargs):
                    start_normalized = kwargs.pop('start_normalized')
                    end_normalized = kwargs.pop('end_normalized')
                    return "".join([",%6.2f" % float(start_normalized.get(bug_type, bug_type_weight)),
                                    ",%6.2f" % float(end_normalized.get(bug_type, bug_type_weight))])

                def add_csv_board_weights(key, **kwargs):
                    board_metric_weights = kwargs.pop('board_metric_weights')
                    return "".join([",%6.2f" % float(board_metric_weights.get(key))])

                for p in profile_list:
                    profile_str = "%s,%s,%s,%d,%d,%s,%s,%d,%d,%d" % \
                                  (p.id, p.name, p.game_type, p.elo_rating, p.generation,
                                   p.parent_a if p.parent_a is not None else "",
                                   p.parent_b if p.parent_b is not None else "", p.wins, p.losses, p.draws)

                    if p.game_type == "Extended":
                        board_metric_strs = p.board_metric_weights.iterate_over_weights_result(
                            add_csv_board_weights, [], board_metric_weights=p.board_metric_weights)
                        profile_str += reduce((lambda a, b: a + b), board_metric_strs).replace(" ", "")

                    sn = p.start_metric_weights.get_normalized()
                    en = p.end_metric_weights.get_normalized()
                    data_strs = self.metric_weights_cls.iterate_over_weights_result(
                        add_csv_norm_weights, [], start_normalized=sn, end_normalized=en)

                    profile_str += reduce((lambda a, b: a + b), data_strs).replace(" ", "")
                    f.write(profile_str)
                    f.write("\n")

            self.log("Analyze end.")

    def battle(self, white_profile_path=None, black_profile_path=None):
        if white_profile_path is None and black_profile_path is None:
            return self.battle(self.trainer_settings.white_profile_path, self.trainer_settings.black_profile_path)
        if white_profile_path.isspace():
            raise ValueError("Invalid white_profile_path.")
        if black_profile_path.isspace():
            raise ValueError("Invalid black_profile_path.")

        self.start_time = datetime.datetime.now()

        for i in range(self.trainer_settings.battle_repeat):
            # Load, then battle profiles:
            white_profile = self.read_profile(white_profile_path)
            black_profile = self.read_profile(black_profile_path)

            self.battle_profiles(white_profile, black_profile, report_moves=True)

            # Save Profiles
            self.write_profile(white_profile_path, white_profile)
            self.write_profile(black_profile_path, black_profile)

    def battle_royale(self, *args):
        if len(args) == 0:
            args = [self.trainer_settings.profile_path, self.trainer_settings.max_battles,
                    self.trainer_settings.max_draws, self.trainer_settings.bulk_battle_time_limit,
                    self.trainer_settings.battle_shuffle_profiles, self.trainer_settings.max_concurrent_battles]
            return self.battle_royale(*args)
        else:
            path, max_battles, max_draws, time_limit, shuffle_profiles, max_concurrent_battles = args

            if path.isspace():
                raise ValueError("Invalid path.")
            if max_battles < 1 and max_battles != self.trainer_settings.max_max_battles:
                raise ValueError("Invalid max_battles.")
            if max_draws < 1:
                raise ValueError("Invalid max_draws.")
            if max_concurrent_battles < 1 and max_concurrent_battles != self.trainer_settings.max_concurrent_battles:
                raise ValueError("Invalid max_concurrent_battles.")

        self.start_time = datetime.datetime.now()
        br_start = datetime.datetime.now()

        profile_list = self.load_profiles(path)
        combinations = len(profile_list) * (len(profile_list) - 1)

        if max_battles == self.trainer_settings.max_max_battles:
            max_battles = combinations
        max_battles = min(max_battles, combinations)
        total = max_battles

        global trainer_counter
        trainer_counter = TrainerCounter(init_completed=0, init_remaining=total)

        time_remaining = datetime.timedelta(seconds=self.trainer_settings.battle_time_limit.seconds * total)
        timeout_remaining = time_limit - (datetime.datetime.now() - br_start)
        ts = self.to_string
        eta = ts(timeout_remaining) if timeout_remaining < time_remaining else ts(time_remaining)
        self.log("Battle Royale start, ETA: %s." % eta)

        white_profiles = list(sorted(profile_list, key=lambda x: x.elo_rating))
        black_profiles = list(sorted(profile_list, key=lambda x: x.elo_rating, reverse=True))
        matches = list(set((wp, bp) for wp in white_profiles for bp in black_profiles if wp != bp))

        if shuffle_profiles:
            matches = self.shuffle(matches)

        # Generate list of lists of parameters for calls to simulate_match:
        args = (max_draws, path, time_limit, br_start)
        # noinspection PyTypeChecker
        inputs = [(self, match) + args for match in matches]

        # Spawn simulate_tier processes across "max_parallelism" cores:
        max_parallelism = self.get_max_parallelism(max_concurrent_battles)
        chunk_size = len(inputs) // max_parallelism

        with mp.Pool(max_parallelism, initargs=(trainer_counter,)) as pool:
            for battle_result in pool.imap_unordered(work_battle_royale, inputs, chunksize=chunk_size):
                # Terminate the entire pool if a timeout occurs:
                if battle_result == -1:
                    pool.terminate()
                    break

        if time_limit - (datetime.datetime.now() - br_start) <= datetime.timedelta.min:
            self.log("Battle Royale time-out.")
        self.log("Battle Royale end, elapsed time: %s." % ts(datetime.datetime.now() - br_start))

        best = list(sorted(profile_list, key=lambda x: x.elo_rating, reverse=True))[0]
        self.log("Battle Royale Highest Elo: %s" % ts(best))

    def cull(self, path=None, keep_count=None, provisional_rules=None):
        if path is None:
            return self.cull(self.trainer_settings.profile_path,
                             self.trainer_settings.cull_keep_count,
                             self.trainer_settings.provisional_rules)
        else:
            if path.isspace():
                raise ValueError("Invalid path.")
            if keep_count < self.trainer_settings.cull_min_keep_count \
                    and keep_count != self.trainer_settings.cull_keep_max:
                raise ValueError("Invalid keep_count.")

            self.start_time = datetime.datetime.now()
            self.log("Cull start.")

            profile_list = self.load_profiles(path)

            if provisional_rules:
                profile_list = [p for p in profile_list if not self.is_provisional(p)]

            profile_list = list(sorted(profile_list, key=lambda x: x.elo_rating, reverse=True))

            if keep_count == self.trainer_settings.cull_keep_max:
                keep_count = max(self.trainer_settings.cull_min_keep_count, round(math.sqrt(len(profile_list))))

            if not os.path.exists(path + "Culled"):
                os.mkdir(path + "Culled")

            count = 0
            for p in profile_list:
                if count < keep_count:
                    self.log("Kept %s." % self.to_string(p))
                    count += 1
                else:
                    source_file = "".join([path, str(p.id), ".xml"])
                    dest_file = "".join([path, "Culled/", str(p.id), ".xml"])

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
            profile_list = list(sorted(profile_list, key=lambda x: x.elo_rating))

            for p in profile_list:
                self.log("%s" % self.to_string(p))

            self.log("Enumerate end.")

    def generate(self, path=None, count=None, game_type=None, min_weight=None, max_weight=None):
        if path is None:
            return self.generate(self.trainer_settings.profile_path,
                                 self.trainer_settings.generate_count,
                                 self.trainer_settings.game_type,
                                 self.trainer_settings.generate_min_weight,
                                 self.trainer_settings.generate_max_weight)
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
                file_path = "".join([path, str(profile.id), ".xml"])
                self.write_profile(file_path, profile)
                self.log("Generated %s." % self.to_string(profile))

            self.log("Generate end.")

    def lifecycle(self, path=None, generations=None, battles=None):
        if path is None:
            return self.lifecycle(self.trainer_settings.profile_path,
                                  self.trainer_settings.lifecycle_generations,
                                  self.trainer_settings.lifecycle_battles)
        else:
            if path.isspace():
                raise ValueError("Invalid path.")
            if generations == 0:
                raise ValueError("Invalid generations.")

        self.start_time = datetime.datetime.now()
        lifecycle_start = datetime.datetime.now()
        self.log("Lifecycle start.")

        gen = 1
        while generations == self.trainer_settings.infinite_lifecycle_generations or gen <= generations:
            if generations != 1:
                self.log("Lifecycle generation %d start." % gen)

            # Battle
            if battles != 0:
                for j in range(abs(battles)):
                    if battles < 0:
                        self.tournament(path, self.trainer_settings.max_draws,
                                        self.trainer_settings.bulk_battle_time_limit,
                                        self.trainer_settings.battle_shuffle_profiles,
                                        self.trainer_settings.max_concurrent_battles)
                    elif battles > 0:
                        self.battle_royale(path, self.trainer_settings.max_battles,
                                           self.trainer_settings.max_draws,
                                           self.trainer_settings.bulk_battle_time_limit,
                                           self.trainer_settings.battle_shuffle_profiles,
                                           self.trainer_settings.max_concurrent_battles)

            # Cull & Mate
            self.cull(path, self.trainer_settings.cull_keep_count, self.trainer_settings.provisional_rules)
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
            args = [self.trainer_settings.mate_min_mix, self.trainer_settings.mate_max_mix,
                    self.trainer_settings.mate_parent_count, self.trainer_settings.mate_shuffle_parents,
                    self.trainer_settings.provisional_rules]
            return self.mate(path, *args)
        else:
            if path.isspace():
                raise ValueError("Invalid path.")

            min_mix, max_mix, parent_count, shuffle_parents, provisional_rules = args

            if min_mix > max_mix:
                raise ValueError("Invalid min_mix.")

            too_few = parent_count < self.trainer_settings.mate_min_parent_count
            if too_few and parent_count != self.trainer_settings.mate_parent_max:
                raise ValueError("Invalid parent_count.")

            self.start_time = datetime.datetime.now()
            self.log("Mate start.")

            profiles_list = self.load_profiles(path)

            if provisional_rules:
                profiles_list = [p for p in profiles_list if not self.is_provisional(p)]

            profiles_list = self.shuffle(profiles_list) if shuffle_parents else self.seed(profiles_list)

            max_parents = len(profiles_list) - (len(profiles_list) % 2)
            if parent_count == self.trainer_settings.mate_parent_max:
                parent_count = max_parents

            parent_count = min(parent_count, max_parents)  # No more parents that exist

            if parent_count >= self.trainer_settings.mate_min_parent_count:
                parents = queue.Queue()
                for i, p in enumerate(profiles_list):
                    if i == parent_count:
                        break
                    parents.put(profiles_list[i])

                while parents.qsize() >= 2:
                    parent_a = parents.get()
                    parent_b = parents.get()
                    child = Profile.mate(parent_a, parent_b, min_mix, max_mix, self.trainer_settings.use_original_ga)

                    pa, pb, ch = self.to_string(parent_a), self.to_string(parent_b), self.to_string(child)
                    self.log("Mated %s and %s to sire %s." % (pa, pb, ch))

                    file_path = "".join([path, str(child.id), ".xml"])
                    self.write_profile(file_path, child)

            self.log("Mate end.")

    def tournament(self, *args):
        if len(args) == 0:
            args = [self.trainer_settings.profile_path, self.trainer_settings.max_draws,
                    self.trainer_settings.bulk_battle_time_limit, self.trainer_settings.battle_shuffle_profiles,
                    self.trainer_settings.max_concurrent_battles]
            return self.tournament(*args)
        else:
            path, max_draws, time_limit, shuffle_profiles, max_concurrent_battles = args

            if path.isspace():
                raise ValueError("Invalid path.")
            if max_draws < 1:
                raise ValueError("Invalid max_draws.")
            if max_concurrent_battles < 1 and \
                    max_concurrent_battles != self.trainer_settings.max_max_concurrent_battles:
                raise ValueError("Invalid max_concurrent_battles.")

            self.start_time = datetime.datetime.now()
            tournament_start = datetime.datetime.now()

            profiles = self.load_profiles(path)
            total = len(profiles) - 1

            global trainer_counter
            trainer_counter = TrainerCounter(init_completed=0, init_remaining=total)

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
                gimme_profile = current_tier[-1] if len(current_tier) % 2 != 0 else None

                # Generate list of lists of parameters for calls to simulate_tier_battle:
                args = (current_tier, max_draws, path, time_limit, tournament_start)
                # noinspection PyTypeChecker
                inputs = [(self, i) + args for i in range(len(current_tier) // 2)]

                # Spawn simulate_tier processes across "max_parallelism" cores:
                max_parallelism = self.get_max_parallelism(max_concurrent_battles)
                chunk_size = len(inputs) // max_parallelism

                with mp.Pool(max_parallelism, initargs=(trainer_counter,)) as pool:
                    for battle_result in pool.imap_unordered(work_tournament, inputs, chunksize=chunk_size):
                        # Terminate the entire pool if a timeout occurs:
                        if battle_result == -1:
                            pool.terminate()
                            break
                        else:
                            winners.extend(battle_result)

                self.log("Tournament tier %d end." % tier)
                tier += 1

                current_tier = winners
                if gimme_profile:
                    current_tier.append(gimme_profile)

                if time_limit - (datetime.datetime.now() - tournament_start) <= datetime.timedelta.min:
                    self.log("Tournament time-out.")
                    break

            self.log("Tournament end, elapsed time: %s." % ts(datetime.datetime.now() - tournament_start))

            if len(current_tier) == 1 and current_tier[0] is not None:
                winner = current_tier[0]
                self.log("Tournament Winner: %s" % ts(winner))

            profiles = self.load_profiles(path)  # re-load updated profiles
            best = list(sorted(profiles, key=lambda x: x.elo_rating, reverse=True))[0]
            self.log("Tournament Highest Elo: %s" % ts(best))
