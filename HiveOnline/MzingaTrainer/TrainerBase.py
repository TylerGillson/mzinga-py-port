import asyncio
import cProfile
import datetime
import gc
import random
import os
import multiprocessing as mp
from typing import List

from MzingaShared.Core.GameBoard import GameBoard
from MzingaShared.Core.AI.BoardMetricWeights import BoardMetricWeights as BoardMetricWeightsCls
from MzingaShared.Core.AI.MetricWeights import MetricWeights as MetricWeightsCls
from MzingaShared.Core.AI.GameAI import GameAI
from MzingaShared.Core.AI.GameAIConfig import GameAIConfig
from MzingaTrainer.Profile import Profile
from MzingaTrainer import EloUtils
from MzingaTrainer.EloUtils import EloUtils as EloUtilsCls
from MzingaTrainer.TrainerSettings import TrainerSettings
from MzingaTrainer import Trainer

GameResults = ["Loss", "Draw", "Win"]

run_profile = False


class TrainerBase(object):
    _start_time = None
    _settings = None
    _random = None

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
        self.metric_weights_cls = MetricWeightsCls(self._settings.game_type)

    def get_max_parallelism(self, max_concurrent_battles):
        max_parallelism = mp.cpu_count() \
            if max_concurrent_battles == self.trainer_settings.max_max_concurrent_battles \
            else max_concurrent_battles
        return max_parallelism

    def simulate_match(self, match, max_draws, path, time_limit, br_start):
        ts = self.to_string
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
                round_result = self.battle_profiles(w_profile, b_profile, report_moves=True)

                self.log("Battle Royale round %d end." % rounds + 1)
                rounds += 1

                if rounds >= max_draws and round_result == "Draw":
                    self.log("Battle Royale match draw-out.")
                    break

        w_s, b_s = ts(w_profile), ts(b_profile)
        self.log("Battle Royale match end %s vs. %s." % (w_s, b_s))

        # Save Profiles
        w_profile_path = "".join([path, str(w_profile.id), ".xml"])
        self.write_profile(w_profile_path, w_profile)

        b_profile_path = "".join([path, str(b_profile.id), ".xml"])
        self.write_profile(b_profile_path, b_profile)

        # Display progress:
        Trainer.trainer_counter.update()
        completed, remaining = Trainer.trainer_counter.values

        timeout_remaining = time_limit - (datetime.datetime.now() - br_start)
        progress, time_remaining = self.get_progress(br_start, completed, remaining)
        eta = ts(timeout_remaining) if timeout_remaining < time_remaining else ts(time_remaining)
        self.log("Battle Royale progress: %6.2f, ETA: %s." % (progress, eta))

        gc.collect()

        if timeout_remaining <= datetime.timedelta.min:
            return -1
        return 1

    def battle_profiles(self, white_profile, black_profile, report_moves=False):
        # Conditionally profile the battle:
        pr = None
        if run_profile:
            pr = cProfile.Profile()
            pr.enable()

        if white_profile is None:
            raise ValueError("Invalid white_profile.")
        if black_profile is None:
            raise ValueError("Invalid black_profile.")
        if white_profile.id == black_profile.id:
            raise ValueError("Profile cannot battle itself.")

        battle_key = "".join([white_profile.name, "_", black_profile.name])

        # Create AIs
        wp_st, wp_end = white_profile.start_metric_weights, white_profile.end_metric_weights
        bp_st, bp_end = black_profile.start_metric_weights, black_profile.end_metric_weights

        white_ai = GameAI(battle_key, GameAIConfig(
            wp_st,
            wp_end,
            self.trainer_settings.trans_table_size,
            white_profile.game_type,
            board_weights=white_profile.board_metric_weights,
            use_heuristics=self.trainer_settings.white_use_heuristics)
        )

        black_ai = GameAI(battle_key, GameAIConfig(
            bp_st,
            bp_end,
            self.trainer_settings.trans_table_size,
            black_profile.game_type,
            board_weights=black_profile.board_metric_weights,
            use_heuristics=self.trainer_settings.black_use_heuristics)
        )

        # Create Game
        kwargs = {
            "board_string": "START",
            "game_type": "Extended" if self.trainer_settings.mixed_game_types else white_ai.game_type,
            "mixed_battle": self.trainer_settings.mixed_game_types,
            "extended_colour": self.trainer_settings.extended_colour,
        }
        game_board = GameBoard(**kwargs)

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
                move = self.get_best_move(game_board, ai)
                game_board.play(move[0])

        except Exception as ex:
            self.log("Battle interrupted with exception: %s" % ex)

        board_state = "Draw" if game_board.game_in_progress else game_board.board_state

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

        # Reset modulated metric weights:
        white_profile.start_metric_weights, white_profile.end_metric_weights = wp_st, wp_end
        black_profile.start_metric_weights, black_profile.end_metric_weights = bp_st, bp_end

        # Prepare for ELO update:
        white_rating = white_profile.elo_rating
        white_k = EloUtils.provisional_k if self.is_provisional(white_profile) else EloUtils.default_k
        black_rating = black_profile.elo_rating
        black_k = EloUtils.provisional_k if self.is_provisional(black_profile) else EloUtils.default_k

        # Update ELO scores:
        white_end_rating, black_end_rating = EloUtilsCls.update_ratings(
            white_rating, black_rating, white_score, black_score, white_k, black_k)
        white_profile.update_record(white_end_rating, white_result)
        black_profile.update_record(black_end_rating, black_result)

        # Output battle result:
        w_s, b_s = self.to_string(white_profile), self.to_string(black_profile)
        if report_moves:
            self.log("Battle end %s %s vs. %s. Turns: %d" % (board_state, w_s, b_s, game_board.current_turn))
        else:
            self.log("Battle end %s %s vs. %s" % (board_state, w_s, b_s))

        # Output profile results:
        if run_profile:
            pr.disable()
            pr.dump_stats('/Users/tylergillson/Desktop/output.prof')

        # Clean up:
        del white_ai, black_ai, game_board
        gc.collect()

        return board_state

    def get_best_move(self, game_board, ai):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if self.trainer_settings.max_depth >= 0:
            future = asyncio.ensure_future(
                ai.get_best_move(
                    game_board,
                    max_depth=self.trainer_settings.max_depth,
                    max_helper_threads=self.trainer_settings.max_helper_threads))
        else:
            # In a mixed battle, adjust the turn time for the Original AI according to a handicap:
            time = self.trainer_settings.turn_max_time
            if self.trainer_settings.mixed_game_types:
                if game_board.current_turn_colour != self.trainer_settings.extended_colour:
                    time *= self.trainer_settings.mixed_game_time_handicap

            future = asyncio.ensure_future(
                ai.get_best_move(
                    game_board,
                    max_time=time,
                    max_helper_threads=self.trainer_settings.max_helper_threads))

        done, _ = loop.run_until_complete(asyncio.wait([future]))
        results = [fut.result() for fut in done]
        return results

    def load_profiles(self, path) -> List[Profile]:
        if path.isspace():
            raise ValueError("Invalid path.")

        files = [f for f in os.listdir(path) if f.endswith(".xml")]
        return [self.read_profile(path + f) for f in files]

    def log(self, output):
        now = datetime.datetime.now()
        elapsed_time = now - self.start_time
        log_str = "%s > %s" % (self.to_string(elapsed_time), output)

        if self.trainer_settings.log_to_file:
            timestamp = self.start_time.strftime("%Y_%m_%d.%H:%M")
            log_path = "".join([self.trainer_settings.profile_path, timestamp, "_log.txt"])

            with open(log_path, "a") as log:
                log.write("".join([log_str, '\n']))
        else:
            print(log_str)

    def simulate_tier_battle(self, i, current_tier, max_draws, path, time_limit, tournament_start):
        winners = []
        ts = self.to_string
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

            white_higher_rank = white_profile.elo_rating < black_profile.elo_rating
            draw_winner_profile = white_profile if white_higher_rank else black_profile

            w_s, b_s = ts(white_profile), ts(black_profile)
            self.log("Tournament match start %s vs. %s." % (w_s, b_s))

            if max_draws == 1:
                round_result = self.battle_profiles(white_profile, black_profile, report_moves=True)
            else:
                rounds = 0
                while round_result == "Draw":
                    self.log("Tournament round %d start." % (rounds + 1))
                    round_result = self.battle_profiles(white_profile, black_profile, report_moves=True)

                    self.log("Tournament round %d end." % (rounds + 1))
                    rounds += 1

                    if rounds >= max_draws and round_result == "Draw":
                        self.log("Tournament match draw-out.")
                        break

            if round_result == "Draw":
                round_result = "WhiteWins" if draw_winner_profile == white_profile else "BlackWins"

            w_s, b_s = ts(white_profile), ts(black_profile)
            self.log("Tournament match end %s vs. %s." % (w_s, b_s))

            # Add winner back into the participant queue
            if round_result == "WhiteWins":
                winners.append(white_profile)
            elif round_result == "BlackWins":
                winners.append(black_profile)

            self.log("Tournament advances %s." % ts(winners[0]))

            # Save Profiles
            white_profile_path = "".join([path, str(white_profile.id), ".xml"])
            self.write_profile(white_profile_path, white_profile)

            black_profile_path = "".join([path, str(black_profile.id), ".xml"])
            self.write_profile(black_profile_path, black_profile)

            timeout_remaining = time_limit - (datetime.datetime.now() - tournament_start)

            Trainer.trainer_counter.update()
            completed, remaining = Trainer.trainer_counter.values
            progress, time_remaining = self.get_progress(tournament_start, completed, remaining)
            eta = ts(timeout_remaining) if timeout_remaining < time_remaining else ts(time_remaining)
            self.log("Tournament progress: %6.2f, ETA: %s." % (progress, eta))

            gc.collect()

            if timeout_remaining <= datetime.timedelta.min:
                return -1
            return winners

    def to_string(self, val):
        if isinstance(val, datetime.timedelta):
            hours, remainder = divmod(val.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return "%d-%d:%d:%d" % (val.days, hours, minutes, seconds)
        elif isinstance(val, Profile):
            if val is None:
                raise ValueError("Invalid profile.")

            prov = "?" if self.is_provisional(val) else ""
            return "%s(%d%s %d/%d/%d)" % (val.name, val.elo_rating, prov, val.wins, val.losses, val.draws)

    def is_provisional(self, profile):
        if profile is None:
            raise ValueError("Invalid profile.")
        return profile.total_games < self.trainer_settings.provisional_game_count

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

        sorted_profiles = list(sorted(profile_list, key=lambda x: x.elo_rating))
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
        total = completed + remaining

        if completed == 0:
            progress = 0.0
            time_remaining = datetime.timedelta.max
        elif remaining == 0:
            progress = 1.0
            time_remaining = datetime.timedelta.min
        else:
            elapsed_time = datetime.datetime.now() - start_time
            elapsed_ms = elapsed_time.total_seconds() * 1000
            avg_ms = elapsed_ms / completed

            progress = completed / total
            time_remaining = datetime.timedelta(milliseconds=avg_ms * remaining)

        return progress, time_remaining
