import sys
import os
from os.path import dirname
sys.path.append(dirname(dirname(dirname(os.getcwd()))))  # Add root directory to PYTHONPATH

import numpy as np
import functools
import datetime

from MzingaShared.Core import EnumUtils
from MzingaShared.Core.EnumUtils import EnumUtils as EnumUtilsCls
from Utils.Events import Broadcaster
from MzingaShared.Core.FixedCache import FixedCache
from MzingaShared.Core.Move import Move
from MzingaShared.Core.MoveSet import MoveSet
from MzingaShared.Core.AI.EvaluatedMove import EvaluatedMove
from MzingaShared.Core.AI.EvaluatedMoveCollection import EvaluatedMoveCollection
from MzingaShared.Core.AI.ListExtensions import ListExtensions
from MzingaShared.Core.AI.MetricWeights import MetricWeights
from MzingaShared.Core.AI.TranspositionTable import TranspositionTable, TranspositionTableEntry, \
                                                    TranspositionTableEntryType


class BestMoveFoundEventArgs:
    def __init__(self, move, depth, score):
        self.Move = move
        self.Depth = depth
        self.Score = score


class BestMoveParams:
    def __init__(self, max_search_depth, max_helper_threads, best_move):
        self.MaxSearchDepth = max_search_depth
        self.MaxHelperThreads = max_helper_threads
        self.BestMove = best_move


class GameAI:
    BestMoveFound = Broadcaster()

    def on_best_move_found(self, best_move_params, evaluated_move):
        if evaluated_move is None:
            raise ValueError("Invalid evaluated_move.")

        if evaluated_move != best_move_params.BestMove:
            # Fire GameEngine.on_best_move_found func:
            self.BestMoveFound.on_change.fire(
                BestMoveFoundEventArgs(evaluated_move.move, evaluated_move.depth, evaluated_move.score_after_move),
                handler_key=1
            )
            best_move_params.BestMove = evaluated_move

    BestMoveFound.on_change += on_best_move_found  # add a listener to the event

    StartMetricWeights = None
    EndMetricWeights = None
    MaxMaxBranchingFactor = 500
    DefaultBoardScoresCacheSize = 516240
    QuiescentSearchMaxDepth = 3  # To prevent runaway stack overflows
    MaxDepth = 10

    _max_branching_factor = MaxMaxBranchingFactor  # To prevent search explosion
    _transposition_table = None
    _cached_board_scores = FixedCache(DefaultBoardScoresCacheSize)

    def __init__(self, config=None):
        if config:
            self.StartMetricWeights = config.StartMetricWeights.clone() \
                if config.StartMetricWeights else MetricWeights()
            self.EndMetricWeights = config.EndMetricWeights.clone() if config.EndMetricWeights else MetricWeights()

            if config.TranspositionTableSizeMB is not None:
                if config.TranspositionTableSizeMB <= 0:
                    raise ValueError("Invalid config.TranspositionTableSizeMB.")
                self._transposition_table = TranspositionTable(config.TranspositionTableSizeMB * 1024 * 1024)
            else:
                self._transposition_table = TranspositionTable()

            if config.MaxBranchingFactor is not None:
                if config.MaxBranchingFactor <= 0:
                    raise ValueError("Invalid config.MaxBranchingFactor.")
                self._max_branching_factor = config.MaxBranchingFactor
        else:
            self.StartMetricWeights = MetricWeights()
            self.EndMetricWeights = MetricWeights()
            self._transposition_table = TranspositionTable()

    def reset_caches(self):
        self._transposition_table.clear()
        self._cached_board_scores.clear()

    # region Move Evaluation
    def get_best_move(self, game_board, **kwargs):
        return self.get_best_move_async(game_board, **kwargs)

    async def get_best_move_async(self, game_board, **kwargs):
        max_depth = self.MaxDepth if 'max_depth' not in kwargs else int(kwargs.pop('max_depth'))
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
        self.BestMoveFound.on_change.fire(self, best_move_params, evaluated_moves.best_move, handler_key=0)
        return best_move_params.BestMove.move

    async def evaluate_moves_async(self, game_board, best_move_params, **kwargs):
        timeout = kwargs.get('max_time') if 'max_time' in kwargs else None
        start_time = kwargs.get('start_time') if 'start_time' in kwargs else None

        moves_to_evaluate = EvaluatedMoveCollection()
        best_move = None

        # Try to get cached best move if available
        key = game_board.zobrist_key
        flag, t_entry = self._transposition_table.try_lookup(key)
        if flag and t_entry.BestMove is not None:
            best_move = EvaluatedMove(t_entry.BestMove, t_entry.Value, t_entry.Depth)
            self.BestMoveFound.on_change.fire(self, best_move_params, best_move, handler_key=0)

        if best_move is not None and best_move.score_after_move == float("inf"):
            # Winning move, don't search
            moves_to_evaluate.add(evaluated_move=best_move)
            return moves_to_evaluate

        valid_moves = self.get_presorted_valid_moves(game_board, best_move)

        # If necessary, convert each entry to an EvaluatedMove:
        if isinstance(valid_moves[0], Move):
            valid_moves = list(map(lambda x: EvaluatedMove(x), valid_moves))

        moves_to_evaluate.add(evaluated_moves=valid_moves, re_sort=False)

        if moves_to_evaluate.count <= 1 or best_move_params.MaxSearchDepth == 0:
            # No need to search
            return moves_to_evaluate

        # Iterative search
        depth = 1 + max(0, moves_to_evaluate.best_move.depth)
        while depth <= best_move_params.MaxSearchDepth:
            if timeout:
                if datetime.datetime.now() > start_time + timeout:
                    break

            # "Re-sort" moves to evaluate based on the next iteration
            moves_to_evaluate = await self.evaluate_moves_to_depth_async(game_board, depth, moves_to_evaluate, **kwargs)

            # Fire best_move_found for current depth
            self.BestMoveFound.on_change.fire(self, best_move_params, moves_to_evaluate.best_move, handler_key=0)

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
        evaluated_moves = EvaluatedMoveCollection()
        first_move = True

        timeout = kwargs.get('max_time') if 'max_time' in kwargs else None
        start_time = kwargs.get('start_time') if 'start_time' in kwargs else None

        for move_to_evaluate in moves_to_evaluate.get_enumerator():
            update_alpha = False
            game_board.trusted_play(move_to_evaluate.move)

            if first_move:
                # Full window search
                value = -1 * await self.principal_variation_search_async(
                    game_board, depth - 1, -beta, -alpha, -colour, "Default", **kwargs)
                update_alpha = True
                first_move = False
            else:
                # Null window search
                value = -1 * await self.principal_variation_search_async(
                    game_board, depth - 1, -alpha - np.finfo(float).eps, -alpha, -colour, "Default", **kwargs)

                if value is not None and alpha < value < beta:
                    # Re-search with full window
                    value = -1 * await self.principal_variation_search_async(
                        game_board, depth - 1, -beta, -alpha, -colour, "Default", **kwargs)

                    update_alpha = True

            game_board.undo_last_move()

            if value is None:
                # Cancel occurred during evaluation
                return EvaluatedMoveCollection(move_to_evaluate, False)

            evaluated_move = EvaluatedMove(move_to_evaluate.move, value, depth)
            evaluated_moves.add(evaluated_move=evaluated_move)

            if update_alpha:
                alpha = max(alpha, value)

            if best_value is None or value >= best_value:
                best_value = value

            if best_value >= beta:
                break  # A winning move has been found, since beta is always infinity in this function

            if timeout:
                if datetime.datetime.now() > start_time + timeout:
                    break

        key = game_board.zobrist_key
        t_entry = TranspositionTableEntry()

        if best_value <= alpha_original:
            # Losing move since alpha_original os negative infinity in this function
            t_entry.Type = TranspositionTableEntryType.UpperBound
        else:
            # Move is a lower bound winning move if best_value >= beta
            # (always infinity in this function), otherwise it's exact
            t_entry.Type = TranspositionTableEntryType.LowerBound \
                if best_value >= beta else TranspositionTableEntryType.Exact
            t_entry.BestMove = evaluated_moves.best_move.move

        t_entry.Value = best_value
        t_entry.Depth = depth

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
        if flag and t_entry.Depth >= depth:
            if t_entry.Type == TranspositionTableEntryType.Exact:
                return t_entry.Value
            elif t_entry.Type == TranspositionTableEntryType.LowerBound:
                alpha = max(alpha, t_entry.Value)
            elif t_entry.Type == TranspositionTableEntryType.UpperBound:
                beta = min(beta, t_entry.Value)

            if alpha >= beta:
                return t_entry.Value

        if depth == 0 or game_board.game_is_over:
            return await self.quiescence_search_async(game_board, self.QuiescentSearchMaxDepth, alpha, beta, colour)

        best_value = None
        best_move = t_entry.BestMove if t_entry else None

        moves = self.get_presorted_valid_moves(game_board, best_move)
        first_move = True

        for move in ListExtensions.get_enumerable_by_order_type(moves, order_type):
            update_alpha = False
            game_board.trusted_play(move)

            if first_move:
                # Full window search
                value = -1 * await self.principal_variation_search_async(
                    game_board, depth - 1, -beta, -alpha, -colour, order_type)
                update_alpha = True
                first_move = False
            else:
                # Null window search
                value = -1 * await self.principal_variation_search_async(
                    game_board, depth - 1, -alpha - np.finfo(float).eps, -alpha, -colour, order_type)

                if value is not None and alpha < value < beta:
                    # Re-search with full window
                    value = -1 * await self.principal_variation_search_async(
                        game_board, depth - 1, -beta, -alpha, -colour, order_type)
                    update_alpha = True

            game_board.undo_last_move()

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
                if datetime.datetime.now() > start_time + timeout:
                    break

        if best_value is not None:
            t_entry = TranspositionTableEntry()

            if best_value <= alpha_original:
                t_entry.Type = TranspositionTableEntryType.UpperBound
            else:
                t_entry.Type = TranspositionTableEntryType.LowerBound \
                    if best_value >= beta else TranspositionTableEntryType.Exact
                t_entry.BestMove = best_move

            t_entry.Value = best_value
            t_entry.Depth = depth
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

            if valid_moves.count > self._max_branching_factor:
                # Too many moves, reduce branching factor
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
        if game_board.is_noisy_move(a) and not game_board.is_noisy_move(b):
            return -1
        elif game_board.is_noisy_move(b) and not game_board.is_noisy_move(a):
            return 1

        return 0
    # endregion

    # region Quiescence Search
    async def quiescence_search_async(self, game_board, depth, alpha, beta, colour):
        best_value = colour * self.calculate_board_score(game_board)
        alpha = max(alpha, best_value)

        if alpha >= beta or depth == 0 or game_board.game_is_over:
            return best_value

        for move in game_board.get_valid_moves():
            if game_board.is_noisy_move(move):
                game_board.trusted_play(move)
                value = -1 * await self.quiescence_search_async(game_board, depth - 1, -beta, -alpha, -colour)
                game_board.undo_last_move()

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
            if game_board.BoardState == "WhiteWins":
                return float("inf")
            elif game_board.BoardState == "BlackWins":
                return float("-inf")
            elif game_board.BoardState == "Draw":
                return 0.0

            key = game_board.zobrist_key

            flag, score = self._cached_board_scores.try_lookup(key)
            if flag:
                return score

            board_metrics = game_board.get_board_metrics()
            score = self.calculate_board_score(None, board_metrics, self.StartMetricWeights, self.EndMetricWeights)
            self._cached_board_scores.store(key, score)

            return score
        elif start_weights and end_weights:
            end_score = self.calculate_board_score(None, board_metrics, end_weights=end_weights)

            if board_metrics.PiecesInHand == 0:
                # In "end-game", no need to blend
                return end_score
            else:
                # Pieces still in hand, blend start and end scores
                start_score = self.calculate_board_score(None, board_metrics, start_weights=start_weights)

                start_ratio = board_metrics.PiecesInHand / (board_metrics.PiecesInHand + board_metrics.PiecesInPlay)
                end_ratio = 1 - start_ratio

                return (start_ratio * start_score) + (end_ratio * end_score)
        else:
            score = 0
            mw = start_weights if start_weights is not None else end_weights

            for piece_name in EnumUtils.PieceNames:
                if piece_name == 'INVALID':
                    continue

                bug_type = EnumUtilsCls.get_bug_type(piece_name)
                colour_value = 1.0 if EnumUtilsCls.get_colour(piece_name) == "White" else -1.0

                score += colour_value * mw.get(bug_type, "InPlayWeight") * board_metrics[piece_name].InPlay
                score += colour_value * mw.get(bug_type, "IsPinnedWeight") * board_metrics[piece_name].IsPinned
                score += colour_value * mw.get(bug_type, "IsCoveredWeight") * board_metrics[piece_name].IsCovered
                score += colour_value * mw.get(bug_type, "NoisyMoveWeight") * board_metrics[piece_name].NoisyMoveCount
                score += colour_value * mw.get(bug_type, "QuietMoveWeight") * board_metrics[piece_name].QuietMoveCount
                score += colour_value * mw.get(bug_type, "FriendlyNeighborWeight") \
                                      * board_metrics[piece_name].FriendlyNeighborCount
                score += colour_value * mw.get(bug_type, "EnemyNeighborWeight") \
                                      * board_metrics[piece_name].EnemyNeighborCount
            return score
