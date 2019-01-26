import sys

try:
    import numpy as np
    eps = np.finfo(float).eps
except ModuleNotFoundError:
    eps = sys.float_info.min

import functools
import datetime

from MzingaShared.Core import EnumUtils
from MzingaShared.Core.EnumUtils import EnumUtils as EnumUtilsCls
from MzingaShared.Core.FixedCache import FixedCache
from MzingaShared.Core.Move import Move
from MzingaShared.Core.MoveSet import MoveSet
from MzingaShared.Core.AI.BoardMetricWeights import BoardMetricWeights
from MzingaShared.Core.AI.EvaluatedMove import EvaluatedMove
from MzingaShared.Core.AI.EvaluatedMoveCollection import EvaluatedMoveCollection
from MzingaShared.Core.AI.ListExtensions import ListExtensions
from MzingaShared.Core.AI.MetricWeights import MetricWeights
from MzingaShared.Core.AI.TranspositionTable import TranspositionTable, \
                                                    TranspositionTableEntry, TranspositionTableEntryType
from Utils.Events import Broadcaster

debug = False
debug_log_path = "/Users/tylergillson/Dropbox/UofC/F2018/CPSC.502.06/MzingaPorted/HiveOnline/MzingaTrainer/Profiles/ExtendedProfiles/"


class BestMoveFoundEventArgs(object):
    __slots__ = "move", "depth", "score"

    def __init__(self, move, depth, score):
        self.move = move
        self.depth = depth
        self.score = score


class BestMoveParams(object):
    __slots__ = "max_search_depth", "max_helper_threads", "best_move"

    def __init__(self, max_search_depth, max_helper_threads, best_move):
        self.max_search_depth = max_search_depth
        self.max_helper_threads = max_helper_threads
        self.best_move = best_move


class GameAI:
    best_move_found = Broadcaster()

    def on_best_move_found(self, best_move_params, evaluated_move):
        if evaluated_move is None:
            raise ValueError("Invalid evaluated_move.")

        if evaluated_move != best_move_params.best_move:
            # Fire GameEngine.on_best_move_found func:
            self.best_move_found.on_change.fire(
                BestMoveFoundEventArgs(evaluated_move.move, evaluated_move.depth, evaluated_move.score_after_move),
                handler_key=1
            )
            best_move_params.best_move = evaluated_move

    best_move_found.on_change += on_best_move_found  # add a listener to the event

    start_metric_weights = None
    end_metric_weights = None
    max_max_branching_factor = 500
    default_board_scores_cache_size = 516240
    quiescent_search_max_depth = 3  # To prevent runaway stack overflows
    max_depth = 3  # 10
    game_type = None

    _max_branching_factor = max_max_branching_factor  # To prevent search explosion
    _transposition_table = None
    _cached_board_scores = FixedCache(default_board_scores_cache_size)

    @property
    def transposition_table_hits(self):
        return self._transposition_table.metrics.hits

    @property
    def cached_board_score_hits(self):
        return self._cached_board_scores.metrics.hits

    def __init__(self, battle_key, config=None):
        self.battle_key = battle_key
        self.use_extended = True

        if config:
            self.game_type = config.game_type

            self.board_metric_weights = config.board_metric_weights.clone() \
                if config.board_metric_weights else BoardMetricWeights()
            self.start_metric_weights = config.start_metric_weights.clone() \
                if config.start_metric_weights else MetricWeights(self.game_type)
            self.end_metric_weights = config.end_metric_weights.clone() \
                if config.end_metric_weights else MetricWeights(self.game_type)

            if config.transposition_table_size_mb is not None:
                if config.transposition_table_size_mb <= 0:
                    raise ValueError("Invalid config.transposition_table_size_mb.")
                self._transposition_table = TranspositionTable(config.transposition_table_size_mb * 1024 * 1024)
            else:
                self._transposition_table = TranspositionTable()

            if config.max_branching_factor is not None:
                if config.max_branching_factor <= 0:
                    raise ValueError("Invalid config.max_branching_factor.")
                self._max_branching_factor = config.max_branching_factor
        else:
            self.game_type = "Original"
            self.board_metric_weights = BoardMetricWeights()
            self.start_metric_weights = MetricWeights(self.game_type)
            self.end_metric_weights = MetricWeights(self.game_type)
            self._transposition_table = TranspositionTable()

    def reset_caches(self):
        self._transposition_table.clear()
        self._cached_board_scores.clear()

    def log(self, value):
        log_path = "".join([debug_log_path, self.battle_key, "_move_log.txt"])

        with open(log_path, "a") as log:
            log.write("".join([value, '\n']))

    # region Move Evaluation
    def get_best_move(self, game_board, **kwargs):
        return self.get_best_move_async(game_board, **kwargs)

    async def get_best_move_async(self, game_board, **kwargs):
        max_depth = self.max_depth if 'max_depth' not in kwargs else int(kwargs.pop('max_depth'))
        kwargs['start_time'] = datetime.datetime.now()

        if game_board is None:
            raise ValueError("Invalid game_board.")

        if max_depth < 0:
            raise ValueError("Invalid max_depth.")

        if game_board.game_is_over:
            raise Exception("Game is over.")

        best_move_params = BestMoveParams(max_depth, None, None)
        evaluated_moves = await self.evaluate_moves_async(game_board, best_move_params, **kwargs)

        if evaluated_moves.count == 0:
            raise Exception("No moves after evaluation!")

        # Make sure at least one move is reported
        self.best_move_found.on_change.fire(self, best_move_params, evaluated_moves.best_move, handler_key=0)
        if debug:
            self.log("".join(["Returning Best Move: ", str(best_move_params.best_move.move)]))

        return best_move_params.best_move.move

    async def evaluate_moves_async(self, game_board, best_move_params, **kwargs):
        timeout = kwargs.get('max_time') if 'max_time' in kwargs else None
        start_time = kwargs.get('start_time') if 'start_time' in kwargs else None

        moves_to_evaluate = EvaluatedMoveCollection()
        best_move = None

        # Try to get cached best move if available
        key = game_board.zobrist_key
        flag, t_entry = self._transposition_table.try_lookup(key)
        if flag and t_entry.best_move is not None:
            best_move = EvaluatedMove(t_entry.best_move, t_entry.value, t_entry.depth)
            self.best_move_found.on_change.fire(self, best_move_params, best_move, handler_key=0)

        if best_move is not None and best_move.score_after_move == float("inf"):
            # Winning move, don't search
            moves_to_evaluate.add(evaluated_move=best_move)
            return moves_to_evaluate

        valid_moves = self.get_presorted_valid_moves(game_board, best_move)

        # If necessary, convert each entry to an EvaluatedMove:
        if isinstance(valid_moves[0], Move):
            valid_moves = list(map(lambda x: EvaluatedMove(x), valid_moves))

        moves_to_evaluate.add(evaluated_moves=valid_moves, re_sort=False)
        if debug:
            self.log("Get Best Move Top Level:")
            self.log(str(game_board))
            self.log("Outer-most moves_to_evaluate:")
            self.log(str(moves_to_evaluate))

        # No need to search
        if moves_to_evaluate.count <= 1 or best_move_params.max_search_depth == 0:
            return moves_to_evaluate

        # Iterative search
        depth = 1 + max(0, moves_to_evaluate.best_move.depth)
        while depth <= best_move_params.max_search_depth:
            if timeout:
                if datetime.datetime.now() > start_time + timeout:
                    break

            # "Re-sort" moves to evaluate based on the next iteration
            moves_to_evaluate = await self.evaluate_moves_to_depth_async(game_board, depth, moves_to_evaluate, **kwargs)
            if debug:
                self.log("Re-sorted:")
                self.log(str(moves_to_evaluate))

            # Fire best_move_found for current depth
            self.best_move_found.on_change.fire(self, best_move_params, moves_to_evaluate.best_move, handler_key=0)

            if moves_to_evaluate.best_move.score_after_move == float("inf"):
                break  # The best move ends the game, stop searching

            # Prune game-losing moves if possible
            moves_to_evaluate.prune_game_losing_moves()

            if moves_to_evaluate.count <= 1:
                break  # Only one move, no reason to keep looking

            depth = 1 + max(depth, moves_to_evaluate.best_move.depth)

        return moves_to_evaluate

    async def evaluate_moves_to_depth_async(self, game_board, depth, moves_to_evaluate, **kwargs):
        alpha = float("-inf")
        beta = float("inf")
        colour = 1 if game_board.current_turn_colour == "White" else -1
        alpha_original = alpha
        best_value = None
        first_move = True
        evaluated_moves = EvaluatedMoveCollection()

        timeout = kwargs.get('max_time') if 'max_time' in kwargs else None
        start_time = kwargs.get('start_time') if 'start_time' in kwargs else None

        # Optimize loop:
        global eps
        trusted_play = game_board.trusted_play
        undo_last_move = game_board.undo_last_move
        principal_variation_search_async = self.principal_variation_search_async
        now = datetime.datetime.now
        eval_moves_add = evaluated_moves.add

        for move_to_evaluate in moves_to_evaluate.get_enumerator():
            if debug:
                self.log("".join(["Evaluating: ", str(move_to_evaluate)]))

            update_alpha = False
            trusted_play(move_to_evaluate.move)

            if first_move:
                # Full window search
                value = -1 * await principal_variation_search_async(
                    game_board, depth - 1, -beta, -alpha, -colour, "Default", **kwargs)
                update_alpha = True
                first_move = False
            else:
                # Null window search
                value = -1 * await principal_variation_search_async(
                    game_board, depth - 1, -alpha - eps, -alpha, -colour, "Default", **kwargs)

                if value is not None and alpha < value < beta:
                    # Re-search with full window
                    value = -1 * await principal_variation_search_async(
                        game_board, depth - 1, -beta, -alpha, -colour, "Default", **kwargs)

                    update_alpha = True

            undo_last_move()

            # Cancel occurred during evaluation
            if value is None:
                return EvaluatedMoveCollection(move_to_evaluate, False)

            evaluated_move = EvaluatedMove(move_to_evaluate.move, value, depth)
            eval_moves_add(evaluated_move=evaluated_move)

            if update_alpha:
                alpha = max(alpha, value)

            if best_value is None or value >= best_value:
                best_value = value

            if best_value >= beta:
                break  # A winning move has been found, since beta is always infinity in this function

            if timeout:
                if now() > start_time + timeout:
                    break

        key = game_board.zobrist_key
        t_entry = TranspositionTableEntry()

        if best_value <= alpha_original:
            # Losing move since alpha_original is negative infinity in this function
            t_entry.type = TranspositionTableEntryType.upper_bound
        else:
            # Move is a lower bound winning move if best_value >= beta
            # (always infinity in this function), otherwise it's exact
            t_entry.type = TranspositionTableEntryType.lower_bound \
                if best_value >= beta else TranspositionTableEntryType.exact
            t_entry.best_move = evaluated_moves.best_move.move

        t_entry.value = best_value
        t_entry.depth = depth
        self._transposition_table.store(key, t_entry)
        return evaluated_moves
    # end region

    # region Principal Variation Search
    async def principal_variation_search_async(self, game_board, depth, alpha, beta, colour, order_type, **kwargs):
        alpha_original = alpha
        key = game_board.zobrist_key

        timeout = kwargs.get('max_time') if 'max_time' in kwargs else None
        start_time = kwargs.get('start_time') if 'start_time' in kwargs else None

        flag, t_entry = self._transposition_table.try_lookup(key)
        if flag and t_entry.depth >= depth:
            if t_entry.type == TranspositionTableEntryType.exact:
                return t_entry.value
            elif t_entry.type == TranspositionTableEntryType.lower_bound:
                alpha = max(alpha, t_entry.value)
            elif t_entry.type == TranspositionTableEntryType.upper_bound:
                beta = min(beta, t_entry.value)

            if alpha >= beta:
                return t_entry.value

        if depth == 0 or game_board.game_is_over:
            return await self.quiescence_search_async(game_board, self.quiescent_search_max_depth, alpha, beta, colour)

        best_value = None
        best_move = t_entry.best_move if t_entry else None
        first_move = True
        moves = self.get_presorted_valid_moves(game_board, best_move)
        if debug:
            self.log("PVS Moves: ")
            self.log(str(moves))

        # Optimize loop:
        global eps
        en_moves = ListExtensions.get_enumerable_by_order_type(moves, order_type) if order_type != "Default" else moves
        trusted_play = game_board.trusted_play
        undo_last_move = game_board.undo_last_move
        principal_variation_search_async = self.principal_variation_search_async
        now = datetime.datetime.now

        for move in en_moves:
            update_alpha = False
            trusted_play(move)

            if first_move:
                # Full window search
                value = -1 * await principal_variation_search_async(
                    game_board, depth - 1, -beta, -alpha, -colour, order_type)
                update_alpha = True
                first_move = False
            else:
                # Null window search
                value = -1 * await principal_variation_search_async(
                    game_board, depth - 1, -alpha - eps, -alpha, -colour, order_type)

                if value is not None and alpha < value < beta:
                    # Re-search with full window
                    value = -1 * await principal_variation_search_async(
                        game_board, depth - 1, -beta, -alpha, -colour, order_type)
                    update_alpha = True

            undo_last_move()

            if value is None:
                return None

            if update_alpha:
                alpha = max(alpha, value)

            if best_value is None or value >= best_value:
                best_value = value
                best_move = move

            if best_value >= beta:
                break

            if timeout:
                if now() > start_time + timeout:
                    break

        if best_value is not None:
            t_entry = TranspositionTableEntry()

            if best_value <= alpha_original:
                t_entry.type = TranspositionTableEntryType.upper_bound
            else:
                t_entry.type = TranspositionTableEntryType.lower_bound \
                    if best_value >= beta else TranspositionTableEntryType.exact
                t_entry.best_move = best_move

            t_entry.value = best_value
            t_entry.depth = depth
            self._transposition_table.store(key, t_entry)

        return best_value
    # endregion

    # region Pre-Sorted Moves
    def get_presorted_valid_moves(self, game_board, best_move):
        if isinstance(best_move, EvaluatedMove):
            bm = best_move.move if best_move else None
            valid_moves = self.get_presorted_valid_moves(game_board, bm)
            evaluated_moves = []
            for move in valid_moves:
                evaluated_moves.append(best_move if move == bm else EvaluatedMove(move))
            return evaluated_moves

        elif isinstance(best_move, Move) or best_move is None:
            valid_moves = game_board.get_valid_moves()
            valid_moves = sorted(
                valid_moves,
                key=functools.cmp_to_key(lambda x, y: self.pre_sort_moves(x, y, game_board, best_move))
            )
            valid_moves = MoveSet(moves_list=valid_moves)

            # Too many moves, reduce branching factor:
            if valid_moves.count > self._max_branching_factor:
                valid_moves.remove_range(self._max_branching_factor)
            return valid_moves
        else:
            raise ValueError("Invalid best_move.")

    @staticmethod
    def pre_sort_moves(a, b, game_board, best_move):
        # Put the best move from a previous search first
        if best_move is not None:
            if a == best_move:
                return -1
            elif b == best_move:
                return 1

        # Put noisy moves first
        noisy_a = game_board.is_noisy_move(a)
        noisy_b = game_board.is_noisy_move(b)

        if noisy_a and not noisy_b:
            return -1
        elif noisy_b and not noisy_a:
            return 1

        return 0
    # endregion

    # region Quiescence Search
    async def quiescence_search_async(self, game_board, depth, alpha, beta, colour):
        best_value = colour * self.calculate_board_score(game_board)
        alpha = max(alpha, best_value)

        if alpha >= beta or depth == 0 or game_board.game_is_over:
            return best_value

        # Optimize away "." accessors:
        is_noisy_move = game_board.is_noisy_move
        trusted_play = game_board.trusted_play
        undo_last_move = game_board.undo_last_move
        quiescence_search_async = self.quiescence_search_async

        valid_moves = game_board.get_valid_moves()
        if debug:
            self.log("Quiescence Search Valid Moves:")
            self.log(str(valid_moves))

        for move in valid_moves:
            if debug:
                self.log("".join(["QS Evaluating: ", str(move)]))

            if move.is_pass:
                continue

            if is_noisy_move(move):
                trusted_play(move)
                value = -1 * await quiescence_search_async(game_board, depth - 1, -beta, -alpha, -colour)
                undo_last_move()

                if value is None:
                    return None

                best_value = max(best_value, value)
                alpha = max(alpha, best_value)

                if alpha >= beta:
                    break

        return best_value
    # endregion

    # region Board Scores
    def calculate_board_score(self, game_board, board_metrics=None, start_weights=None, end_weights=None):
        if game_board:
            # Always score from white's point of view
            if game_board.board_state == "WhiteWins":
                return float("inf")
            elif game_board.board_state == "BlackWins":
                return float("-inf")
            elif game_board.board_state == "Draw":
                return 0.0

            # Attempt to retrieve board score from transposition table:
            key = game_board.zobrist_key
            flag, score = self._cached_board_scores.try_lookup(key)
            if flag:
                return score

            # Ignore extended metrics for the Original profile in a mixed battle:
            if game_board.mixed_battle:
                self.use_extended = game_board.current_turn_colour == game_board.extended_colour

            board_metrics = game_board.get_board_metrics()
            score = self.calculate_board_score(None, board_metrics, self.start_metric_weights, self.end_metric_weights)
            self._cached_board_scores.store(key, score)
            return score

        elif start_weights and end_weights:
            end_score = self.calculate_board_score(None, board_metrics, end_weights=end_weights)

            if board_metrics.pieces_in_hand == 0:
                # In "end-game", no need to blend
                return end_score
            else:
                # Pieces still in hand, blend start and end scores
                start_score = self.calculate_board_score(None, board_metrics, start_weights=start_weights)
                start_ratio = \
                    board_metrics.pieces_in_hand / (board_metrics.pieces_in_hand + board_metrics.pieces_in_play)
                end_ratio = 1 - start_ratio

                return (start_ratio * start_score) + (end_ratio * end_score)
        else:
            score = 0
            mw = start_weights if start_weights is not None else end_weights

            # Optimize away "." accessors:
            get_bug_type = EnumUtilsCls.get_bug_type
            get_colour = EnumUtilsCls.get_colour
            get = mw.get

            # Optionally compute extended board metrics:
            if self.game_type == "Extended" and self.use_extended:
                bmw_get = self.board_metric_weights.get
                queen_bee_life_weight = bmw_get("queen_bee_life_weight")
                queen_bee_tight_spaces_weight = bmw_get("queen_bee_tight_spaces_weight")
                noisy_ring_weight = bmw_get("noisy_ring_weight")

                score += board_metrics.black_queen_life * -queen_bee_life_weight
                score += board_metrics.white_queen_life * queen_bee_life_weight
                score += board_metrics.black_queen_tight_spaces * -queen_bee_tight_spaces_weight
                score += board_metrics.white_queen_tight_spaces * queen_bee_tight_spaces_weight
                score += board_metrics.black_noisy_ring * -noisy_ring_weight
                score += board_metrics.white_noisy_ring * noisy_ring_weight

            for piece_name in EnumUtils.piece_names:
                if piece_name == 'INVALID':
                    continue

                bug_type = get_bug_type(piece_name)
                colour_value = 1.0 if get_colour(piece_name) == "White" else -1.0

                score += colour_value * get(bug_type, "in_play_weight") * board_metrics[piece_name].in_play
                score += colour_value * get(bug_type, "is_pinned_weight") * board_metrics[piece_name].is_pinned
                score += colour_value * get(bug_type, "is_covered_weight") * board_metrics[piece_name].is_covered
                score += colour_value * get(bug_type, "noisy_move_weight") * board_metrics[piece_name].noisy_move_count
                score += colour_value * get(bug_type, "quiet_move_weight") * board_metrics[piece_name].quiet_move_count
                score += colour_value * get(bug_type, "friendly_neighbour_weight") \
                                      * board_metrics[piece_name].friendly_neighbour_count
                score += colour_value * get(bug_type, "enemy_neighbour_weight") \
                                      * board_metrics[piece_name].enemy_neighbour_count

                # Optionally compute extended piece metrics:
                if self.game_type == "Extended" and self.use_extended:
                    score += colour_value * get(bug_type, "can_make_noisy_ring_weight") \
                        * board_metrics[piece_name].can_make_noisy_ring
                    score += colour_value * get(bug_type, "can_make_defense_ring_weight") \
                        * board_metrics[piece_name].can_make_defense_ring

            return score
