import queue

import timeit
from MzingaShared.Core.ZobristHashC import ZobristHashC

from MzingaShared.Core import Move as MoveCls, EnumUtils
from MzingaShared.Core.BoardMetrics import BoardMetrics
from MzingaShared.Core.CacheMetricsSet import CacheMetricsSet
from MzingaShared.Core.Move import Move
from MzingaShared.Core.MoveSet import MoveSet
from MzingaShared.Core.Piece import Piece
from MzingaShared.Core import Position as PositionCls
from MzingaShared.Core.Position import Position
from MzingaShared.Core.ZobristHash import ZobristHash
from MzingaShared.Core.EnumUtils import Colours, ColoursByInt, PieceNamesByInt, PieceNames, \
                                        EnumUtils as EnumUtilsCls

BoardStates = ["NotStarted", "InProgress", "Draw", "WhiteWins", "BlackWins"]


class Board:
    BoardState = None
    GameType = None

    _board_metrics = None
    _current_turn = 0
    _zobrist_hash = None
    _pieces = []
    _pieces_by_position = {}
    _last_piece_moved = list(PieceNames.keys())[0]  # "INVALID"

    # CACHES
    ValidMoveCacheMetricsSet = None
    ValidMoveCacheResets = 0
    _cached_valid_moves_by_piece = None
    _cached_valid_placement_positions = None
    _visited_placements = set()
    _cached_enemy_queen_neighbors = None

    # END CACHES

    # STATE PROPERTIES
    @property
    def current_turn(self):
        return self._current_turn

    @current_turn.setter
    def current_turn(self, value):
        if value < 0:
            raise ValueError("Invalid value.")

        old_colour = self.current_turn_colour
        self._current_turn = value

        if old_colour != self.current_turn_colour:
            self._zobrist_hash.toggle_turn()  # Turn has changed

        self.reset_caches()

    @property
    def current_turn_colour(self):
        return ColoursByInt.get(self.current_turn % 2)

    @property
    def current_player_turn(self):
        return 1 + (self.current_turn // 2)

    @property
    def game_in_progress(self):
        return self.BoardState in ["NotStarted", "InProgress"]

    @property
    def game_is_over(self):
        return self.BoardState in ["WhiteWins", "BlackWins", "Draw"]

    @property
    def board_string(self):
        s = "%s%c" % (self.BoardState, ';')
        s += "%s[%s]%c" % (self.current_turn_colour, self.current_player_turn, ';')

        for i in range(EnumUtils.NumPieceNames):
            if self._pieces[i] is not None and self._pieces[i].in_play:
                s += "%s%c" % (self._pieces[i], ';')
        return s[:-1:]

    @property
    def zobrist_key(self):
        return self._zobrist_hash.Value

    def __repr__(self):
        return self.board_string
    # END STATE PROPERTIES

    # PIECE ENUMERATION PROPERTIES
    @property
    def current_turn_pieces(self):
        is_white = self.current_turn_colour == "White"
        return EnumUtilsCls.white_piece_names() if is_white else EnumUtilsCls.black_piece_names()

    @property
    def pieces_in_play(self):
        return [PieceNamesByInt.get(i) for i in range(EnumUtils.NumPieceNames)
                if self._pieces[i] is not None and self._pieces[i].in_play]

    @property
    def white_hand(self):
        return [PieceNamesByInt.get(i) for i in range(EnumUtils.NumPieceNames // 2)
                if self._pieces[i] is not None and self._pieces[i].in_play]

    @property
    def black_hand(self):
        return [PieceNamesByInt.get(i) for i in range(EnumUtils.NumPieceNames // 2, EnumUtils.NumPieceNames)
                if self._pieces[i] is not None and self._pieces[i].in_play]
    # END PIECE ENUMERATION PROPERTIES

    # PIECE STATE PROPERTIES
    @property
    def white_queen_in_play(self):
        return self.get_piece("WhiteQueenBee").in_play

    @property
    def black_queen_in_play(self):
        return self.get_piece("BlackQueenBee").in_play

    @property
    def current_turn_queen_in_play(self):
        a = self.current_turn_colour == "White" and self.white_queen_in_play
        b = self.current_turn_colour == "Black" and self.black_queen_in_play
        return a or b

    @property
    def opponent_queen_in_play(self):
        a = self.current_turn_colour == "White" and self.black_queen_in_play
        b = self.current_turn_colour == "Black" and self.white_queen_in_play
        return a or b

    @property
    def last_piece_moved(self):
        return self._last_piece_moved

    @last_piece_moved.setter
    def last_piece_moved(self, value):
        self._last_piece_moved = value
    # END PIECE STATE PROPERTIES

    def init_state_vars(self, game_type):
        self.BoardState = "NotStarted"
        self.GameType = game_type

        self._board_metrics = BoardMetrics()
        self._current_turn = 0

        # print("Cythonized:\t", min(timeit.Timer(ZobristHashC).repeat(number=3)))
        # print("Original:\t", min(timeit.Timer(ZobristHash).repeat(number=3)))

        self._zobrist_hash = ZobristHash()
        self._pieces = []
        self._pieces_by_position = {}
        self._last_piece_moved = list(PieceNames.keys())[0]  # "INVALID"

        # CACHES
        self.ValidMoveCacheMetricsSet = CacheMetricsSet()
        self.ValidMoveCacheResets = 0
        self._cached_valid_moves_by_piece = None
        self._cached_valid_placement_positions = None
        self._visited_placements = set()
        self._cached_enemy_queen_neighbors = None

    def __init__(self, board_string, game_type):
        self.init_state_vars(game_type)
        self.init_pieces()

        # New game constructor
        if board_string == "START":
            return

        if board_string is None or board_string.isspace():
            raise ValueError("Invalid board_string.")

        # Board history string constructor:
        split = board_string.split(';')
        board_state_string = split[0]

        if board_state_string not in BoardStates:
            raise ValueError("%s%s" % ("Couldn't parse board state. ", board_string))

        current_turn_split = list(filter(None, split[1].replace('[', ']').split(']')))
        current_turn_colour_string = current_turn_split[0]

        if current_turn_colour_string not in ColoursByInt.values():
            raise ValueError("%s%s" % ("Couldn't parse current turn colour. ", board_string))

        current_player_turn_string = current_turn_split[1]
        self.current_turn = 2 * (int(current_player_turn_string) - 1) + Colours[current_turn_colour_string]

        parsed_pieces = queue.Queue(EnumUtils.NumPieceNames)
        i = 2
        while i < len(split):
            parsed_pieces.put(Piece(None, piece_string=split[i]))
            i += 1

        while not parsed_pieces.empty():
            parsed_piece = parsed_pieces.get()
            if parsed_piece.in_play:
                if parsed_piece.position.stack > 0 and not self.has_piece_at(parsed_piece.position.get_below()):
                    parsed_pieces.put(parsed_piece)
                else:
                    piece = self.get_piece(parsed_piece.piece_name)
                    self.move_piece(piece, parsed_piece.position, True)

        if not self.is_one_hive():
            raise ValueError("The board_string violates the one-hive rule: %s" % board_string)
        return

    def init_pieces(self):
        for i in range(EnumUtils.NumPieceNames):
            self._pieces.append(Piece(EnumUtils.PieceNamesByInt[i]))

    def has_piece_at(self, position):
        return self.get_piece(position) is not None

    def get_piece_position(self, piece_name):
        if piece_name == list(PieceNames.keys())[0]:  # "INVALID"
            raise ValueError("Invalid piece_name.")
        return self.get_piece(piece_name).position

    def get_piece(self, value) -> Piece:
        if isinstance(value, Position):
            try:
                return self._pieces_by_position[value]
            except KeyError:
                # noinspection PyTypeChecker
                return None
        else:
            return self._pieces[PieceNames[value]]

    def get_piece_on_top(self, value):
        if isinstance(value, Piece):
            while value.piece_above is not None:
                value = value.piece_above
            return value
        else:
            if value is None:
                raise ValueError("Invalid position.")
            value = self.get_piece_on_top_internal(value)
            return value.piece_name if value else list(PieceNames.keys())[0]  # "INVALID"

    def get_piece_on_top_internal(self, position):
        while position.stack > 0:
            position = position.get_below()
        top_piece = self.get_piece(position)
        if top_piece:
            top_piece = self.get_piece_on_top(top_piece)
        return top_piece

    @staticmethod
    def get_piece_on_bottom(piece):
        while piece.piece_below is not None:
            piece = piece.piece_below
        return piece

    def move_piece(self, piece, new_position, update_zobrist=False):
        if not update_zobrist:
            self.move_piece(piece, new_position, True)
        else:
            if piece.in_play:
                self._pieces_by_position[piece.position] = None
                if piece.piece_below is not None:
                    piece.piece_below.piece_above = None
                    piece.piece_below = None

                # Remove from old position
                self._zobrist_hash.toggle_piece(piece.piece_name, piece.position)

            piece.move(new_position)
            if piece.in_play:
                self._pieces_by_position[piece.position] = piece
                if new_position.stack > 0:
                    pos_below = new_position.get_below()
                    piece_below = self.get_piece(pos_below)
                    piece_below.piece_above = piece
                    piece.piece_below = piece_below

                # Add to new position
                self._zobrist_hash.toggle_piece(piece.piece_name, piece.position)

    @staticmethod
    def piece_is_on_top(target_piece):
        return target_piece.piece_above is None

    @staticmethod
    def piece_is_on_bottom(target_piece):
        return target_piece.piece_below is None

    def is_one_hive(self):
        # Whether or not a piece has been found to be part of the hive
        part_of_hive = [0] * EnumUtils.NumPieceNames
        pieces_visited = 0

        # Find a piece on the board to start checking
        starting_piece = None
        for piece_name in list(EnumUtils.PieceNames.keys())[1:]:
            piece = self.get_piece(piece_name)
            if piece is None or piece.in_hand:
                part_of_hive[PieceNames[piece_name]] = True
                pieces_visited += 1
            else:
                part_of_hive[PieceNames[piece_name]] = False
                if starting_piece is None and piece.position.stack == 0:
                    # Save off a starting piece on the bottom
                    starting_piece = piece
                    part_of_hive[PieceNames[piece_name]] = True
                    pieces_visited += 1

        # There is at least one piece on the board
        if starting_piece is not None and pieces_visited < EnumUtils.NumPieceNames:
            pieces_to_look_at = queue.Queue()
            pieces_to_look_at.put(starting_piece)

            while not pieces_to_look_at.empty():
                current_piece = pieces_to_look_at.get()

                # Check all pieces at this stack level
                for i in range(EnumUtils.NumDirections):
                    neighbor = current_piece.position.neighbour_at(i)
                    neighbor_piece = self.get_piece(neighbor)
                    if neighbor_piece is not None and not part_of_hive[PieceNames[neighbor_piece.piece_name]]:
                        pieces_to_look_at.put(neighbor_piece)
                        part_of_hive[PieceNames[neighbor_piece.piece_name]] = True
                        pieces_visited += 1

                # Check for all pieces above this one
                piece_above = current_piece.piece_above
                while piece_above is not None:
                    part_of_hive[PieceNames[piece_above.piece_name]] = True
                    pieces_visited += 1
                    piece_above = piece_above.piece_above

        return pieces_visited == EnumUtils.NumPieceNames

    # METRICS
    def get_board_metrics(self):
        self._board_metrics.reset()
        self._board_metrics.BoardState = self.BoardState

        # Get the metrics for the current turn
        self._set_current_player_metrics()

        # Save off current valid moves/placements since we'll be returning to it
        valid_moves_by_piece = self._cached_valid_moves_by_piece
        self._cached_valid_moves_by_piece = None

        valid_placement_positions = self._cached_valid_placement_positions
        self._cached_valid_placement_positions = None

        enemy_queen_neighbors = self._cached_enemy_queen_neighbors
        self._cached_enemy_queen_neighbors = None

        last_piece_moved = self._last_piece_moved
        self._last_piece_moved = list(PieceNames.keys())[0]  # "INVALID"

        # Spoof going to the next turn to get the opponent's metrics
        self._current_turn += 1
        self._zobrist_hash.toggle_turn()
        self._set_current_player_metrics()
        self._current_turn -= 1
        self._zobrist_hash.toggle_turn()

        # Returned, so reload saved valid moves/placements into cache
        self._last_piece_moved = last_piece_moved
        self._cached_enemy_queen_neighbors = enemy_queen_neighbors
        self._cached_valid_placement_positions = valid_placement_positions
        self._cached_valid_moves_by_piece = valid_moves_by_piece

        return self._board_metrics

    def _set_current_player_metrics(self):
        for piece_name in self.current_turn_pieces:
            target_piece = self.get_piece(piece_name)
            p = self._board_metrics[piece_name]

            if target_piece is not None:
                if target_piece.in_play:
                    self._board_metrics.PiecesInPlay += 1
                    p.InPlay = 1
                else:
                    self._board_metrics.PiecesInHand += 1
                    p.InPlay = 0

                # Set noisy/quiet move counts
                is_pinned, p.NoisyMoveCount, p.QuietMoveCount = self.is_pinned(piece_name)
                is_below = target_piece.in_play and target_piece.piece_above is not None
                p.IsPinned = 1 if is_pinned else 0
                p.IsCovered = 1 if is_below else 0

                # Set neighbor counts
                total, p.FriendlyNeighborCount, p.EnemyNeighborCount = self.count_neighbors(piece=target_piece)

    def count_neighbors(self, piece_name=None, piece=None):
        if piece_name and not piece:
            return self.count_neighbors(piece=self.get_piece(piece_name))
        else:
            friendly_count = 0
            enemy_count = 0

            if piece.in_play:
                for i in range(EnumUtils.NumDirections):
                    neighbor = self.get_piece(piece.position.neighbour_at(i))
                    if neighbor is not None:
                        if neighbor.colour == piece.colour:
                            friendly_count += 1
                        else:
                            enemy_count += 1

            return friendly_count + enemy_count, friendly_count, enemy_count

    def is_pinned(self, piece_name):
        noisy_count = 0
        quiet_count = 0
        is_pinned = True
        is_noisy_move = self.is_noisy_move
        is_quiet_move = self.is_quiet_move

        for move in self.get_valid_moves(piece_name):
            if move.piece_name == piece_name:
                is_pinned = False

            if is_noisy_move(move):
                noisy_count += 1
            else:
                if self.GameType == "Original":
                    quiet_count += 1
                else:
                    if is_quiet_move(piece_name, move):
                        quiet_count += 1

        return is_pinned, noisy_count, quiet_count

    def is_quiet_move(self, piece_name, move):
        if move is None or move.is_pass:
            return False

        moving_piece = self.get_piece(piece_name)
        original_position = self.get_piece_position(piece_name)
        if original_position is None:
            return True

        # Check if any trapped enemy neighbours will be freed by the move:
        trapped_enemy_neighbours = self.get_trapped_neighbours(original_position, enemies_only=True)
        for n in trapped_enemy_neighbours:
            self.move_piece(moving_piece, move.position, False)
            freed = self.can_move_without_breaking_hive(n)
            self.move_piece(moving_piece, original_position, False)
            if freed:
                return False
        return True

    def is_noisy_move(self, move):
        if move is None or move.is_pass:
            return False

        # Determine enemy queen neighbours:
        if self._cached_enemy_queen_neighbors is None:
            self._cached_enemy_queen_neighbors = set()
            enemy_queen_name = "BlackQueenBee" if self.current_turn_colour == "White" else "WhiteQueenBee"
            enemy_queen_position = self.get_piece_position(enemy_queen_name)

            if enemy_queen_position is not None:
                # Add queen's neighboring positions
                add = self._cached_enemy_queen_neighbors.add
                neighbour_at = enemy_queen_position.neighbour_at

                for i in range(EnumUtils.NumDirections):
                    add(neighbour_at(i))

        move_to_adjacent = move.position in self._cached_enemy_queen_neighbors
        piece_already_adjacent = self.get_piece_position(move.piece_name) in self._cached_enemy_queen_neighbors

        if self.GameType == "Original":
            return move_to_adjacent and not piece_already_adjacent
        else:
            moving_piece = self.get_piece(move.piece_name)
            original_position = moving_piece.position

            if original_position is None:
                return move_to_adjacent and not piece_already_adjacent

            # Determine whether the move traps any pieces:
            pre_move_trapped_neighbours = set(self.get_trapped_neighbours(move.position))
            self.move_piece(moving_piece, move.position, False)
            post_move_trapped_neighbours = set(self.get_trapped_neighbours(move.position))
            self.move_piece(moving_piece, original_position, False)

            newly_trapped = list(post_move_trapped_neighbours - pre_move_trapped_neighbours)
            newly_trapped_against_queen = [p for p in newly_trapped if p.position in self._cached_enemy_queen_neighbors]
            return len(newly_trapped_against_queen) > 0

    def get_trapped_neighbours(self, position, enemies_only=False):
        trapped_neighbours = []
        for i in range(EnumUtils.NumDirections):
            n = self.get_piece(position.neighbour_at(i))
            if n is None:
                continue
            if not self.can_move_without_breaking_hive(n):
                if enemies_only and n.colour != self.current_turn_colour:
                    trapped_neighbours.append(n)
                else:
                    trapped_neighbours.append(n)
        return trapped_neighbours
    # END METRICS

    # VALID MOVES
    def get_valid_moves(self, piece_name=None) -> MoveSet:
        if piece_name:
            if self._cached_valid_moves_by_piece is None:
                self._cached_valid_moves_by_piece = MoveSet(size=EnumUtils.NumPieceNames)

            piece_name_index = PieceNames[piece_name]
            cached = self._cached_valid_moves_by_piece[piece_name_index]
            is_pass = False

            if isinstance(cached, Move):
                is_pass = cached.is_pass

            if cached is not None and not is_pass:
                # MoveSet is cached in L1 cache
                self.ValidMoveCacheMetricsSet["ValidMoves." + EnumUtilsCls.get_short_name(piece_name)].hit()
            else:
                # MoveSet is not cached in L1 cache
                self.ValidMoveCacheMetricsSet["ValidMoves." + EnumUtilsCls.get_short_name(piece_name)].miss()

                # Calculate MoveSet
                target_piece = self.get_piece(piece_name)
                moves = self.get_valid_moves_internal(target_piece)
                moves.lock()

                # Populate cache
                self._cached_valid_moves_by_piece[piece_name_index] = moves

            return self._cached_valid_moves_by_piece[piece_name_index]
        else:
            moves = MoveSet()
            add = moves.add
            pass_turn = MoveCls.pass_turn

            if self.game_in_progress:
                list(map(add, list(map(self.get_valid_moves, self.current_turn_pieces))))

                if moves.count == 0:
                    add(pass_turn())

            moves.lock()
            return moves

    def get_valid_moves_internal(self, target_piece):
        # Optimize:
        bug_type = target_piece.bug_type
        colour = target_piece.colour
        in_hand = target_piece.in_hand
        in_play = target_piece.in_play
        piece_name = target_piece.piece_name

        if target_piece is not None and self.game_in_progress:
            if colour == self.current_turn_colour and self.placing_piece_in_order(target_piece):

                not_white_queen = in_hand and piece_name != "WhiteQueenBee"
                not_black_queen = in_hand and piece_name != "BlackQueenBee"
                not_last_moved = piece_name != self.last_piece_moved and in_play

                # Optimize:
                valid_moves = MoveSet()
                add = valid_moves.add
                neighbour_at = PositionCls.origin.neighbour_at
                origin = PositionCls.origin

                # First move must be at the origin and not the White Queen Bee
                if self.current_turn == 0 and colour == "White" and not_white_queen:
                    add(Move(piece_name=piece_name, position=origin))
                    return valid_moves

                # Second move must be around the origin and not the Black Queen Bee
                elif self.current_turn == 1 and colour == "Black" and not_black_queen:

                    for i in range(EnumUtils.NumDirections):
                        # noinspection PyUnresolvedReferences
                        neighbor = neighbour_at(i)
                        add(Move(piece_name=piece_name, position=neighbor))
                    return valid_moves

                elif (in_hand and (self.current_player_turn != 4 or  # Normal turn OR
                      (self.current_player_turn == 4 and  # Turn 4 and AND
                       (self.current_turn_queen_in_play or  # Queen is in play or you're trying to play it
                        (not self.current_turn_queen_in_play and target_piece.bug_type == "QueenBee"))))):
                    # Look for valid new placements
                    return self._get_valid_placements(target_piece)

                elif not_last_moved and self.current_turn_queen_in_play and self.piece_is_on_top(target_piece):

                    if self.can_move_without_breaking_hive(target_piece):
                        # Look for basic valid moves of played pieces who can move
                        if bug_type == "QueenBee":
                            add(self.get_valid_queen_bee_movements(target_piece))
                        elif bug_type == "Spider":
                            add(self.get_valid_spider_movements(target_piece))
                        elif bug_type == "Beetle":
                            add(self.get_valid_beetle_movements(target_piece))
                        elif bug_type == "Grasshopper":
                            add(self.get_valid_grasshopper_movements(target_piece))
                        elif bug_type == "SoldierAnt":
                            add(self.get_valid_soldier_ant_movements(target_piece))
                    return valid_moves
        return MoveSet()

    def _get_valid_placements(self, target_piece):
        valid_moves = MoveSet()
        target_colour = self.current_turn_colour

        if target_piece.colour != target_colour:
            return valid_moves

        if self._cached_valid_placement_positions is None:
            self._cached_valid_placement_positions = set()
            self._visited_placements.clear()

            for i in range(EnumUtils.NumPieceNames):
                piece = self._pieces[i]

                valid_piece = piece is not None and piece.in_play

                # Piece is in play, on the top and is the right color, look through neighbors
                if valid_piece and self.piece_is_on_top(piece) and piece.colour == target_colour:
                    bottom_position = self.get_piece_on_bottom(piece).position
                    self._visited_placements.add(bottom_position)

                    for j in range(EnumUtils.NumDirections):
                        neighbor = bottom_position.neighbour_at(j)

                        # Neighboring position is a potential, verify its neighbors are empty or same color
                        old_len = len(self._visited_placements)
                        self._visited_placements.add(neighbor)

                        if len(self._visited_placements) > old_len and not self.has_piece_at(neighbor):
                            valid_placement = True
                            for k in range(EnumUtils.NumDirections):
                                surrounding_position = neighbor.neighbour_at(k)
                                surrounding_piece = self.get_piece_on_top_internal(surrounding_position)

                                if surrounding_piece is not None and surrounding_piece.colour != target_colour:
                                    valid_placement = False
                                    break

                            if valid_placement:
                                self._cached_valid_placement_positions.add(neighbor)

            self.ValidMoveCacheMetricsSet["ValidPlacements"].miss()
        else:
            self.ValidMoveCacheMetricsSet["ValidPlacements"].hit()

        for valid_placement in self._cached_valid_placement_positions:
            valid_moves.add(Move(piece_name=target_piece.piece_name, position=valid_placement))

        return valid_moves

    def get_valid_queen_bee_movements(self, target_piece):
        # Get all slides one away
        return self.get_valid_slides(target_piece, 1)

    def get_valid_spider_movements(self, target_piece):
        valid_moves = MoveSet()

        # Get all slides up to 2 spots away
        up_to_two = self.get_valid_slides(target_piece, 2)

        if up_to_two.count > 0:
            # Get all slides up to 3 spots away
            up_to_three = self.get_valid_slides(target_piece, 3)

            if up_to_three.count > 0:
                # Get all slides ONLY 3 spots away
                up_to_three.remove(up_to_two)

                if up_to_three.count > 0:
                    valid_moves.add(up_to_three)
        return valid_moves

    def get_valid_beetle_movements(self, target_piece):
        valid_moves = MoveSet()

        # Look in all directions
        for direction in EnumUtils.Directions.keys():
            new_position = target_piece.position.neighbour_at(direction)
            top_neighbor = self.get_piece_on_top_internal(new_position)

            # Get positions to left and right or direction we're heading
            left_of_target = EnumUtilsCls.left_of(direction)
            right_of_target = EnumUtilsCls.right_of(direction)
            left_neighbor_position = target_piece.position.neighbour_at(left_of_target)
            right_neighbor_position = target_piece.position.neighbour_at(right_of_target)

            top_left_neighbor = self.get_piece_on_top_internal(left_neighbor_position)
            top_right_neighbor = self.get_piece_on_top_internal(right_neighbor_position)

            # At least one neighbor is present
            current_height = target_piece.position.stack + 1
            destination_height = top_neighbor.position.stack + 1 if top_neighbor is not None else 0

            top_left_neighbor_height = top_left_neighbor.position.stack + 1 if top_left_neighbor is not None else 0
            top_right_neighbor_height = top_right_neighbor.position.stack + 1 if top_right_neighbor is not None else 0

            # "Take-off" beetle
            current_height -= 1

            same_tier = current_height == 0 and destination_height == 0
            go_down = destination_height < top_left_neighbor_height and destination_height < top_right_neighbor_height
            are_down = current_height < top_left_neighbor_height and current_height < top_right_neighbor_height

            if not (same_tier and top_left_neighbor_height == 0 and top_right_neighbor_height == 0):
                # Logic from http:#boardgamegeek.com/wiki/page/Hive_FAQ#toc9
                if not (go_down and are_down):
                    up_one_tier = new_position.stack == destination_height
                    target_position = new_position if up_one_tier else top_neighbor.position.get_above()
                    target_move = Move(piece_name=target_piece.piece_name, position=target_position)
                    valid_moves.add(target_move)

        return valid_moves

    def get_valid_grasshopper_movements(self, target_piece):
        valid_moves = MoveSet()
        starting_position = target_piece.position

        for direction in EnumUtils.Directions:
            landing_position = starting_position.neighbour_at(direction)
            distance = 0

            while self.has_piece_at(landing_position):
                # Jump one more in the same direction
                landing_position = landing_position.neighbour_at(direction)
                distance += 1

            if distance > 0:
                # Can only move if there's at least one piece in the way
                move = Move(piece_name=target_piece.piece_name, position=landing_position)
                valid_moves.add(move)

        return valid_moves

    def get_valid_soldier_ant_movements(self, target_piece):
        # Get all slides all the way around
        return self.get_valid_slides(target_piece, max_range=None)

    def get_valid_slides(self, target_piece, max_range=None):
        valid_moves = MoveSet()
        starting_position = target_piece.position

        visited_positions = set()
        visited_positions.add(starting_position)
        piece_name = target_piece.piece_name

        self.move_piece(target_piece, None, False)
        self.get_valid_slides_rec(piece_name, starting_position, visited_positions, 0, valid_moves, max_range)
        self.move_piece(target_piece, starting_position, False)

        return valid_moves

    def get_valid_slides_rec(self, target, current_pos, visited_positions, current_range, valid_moves, max_range=None):
        if max_range is None or current_range < max_range:

            # Optimize loop:
            neighbour_at = current_pos.neighbour_at
            right_of = EnumUtilsCls.right_of
            left_of = EnumUtilsCls.left_of
            has_piece_at = self.has_piece_at
            vm_add = valid_moves.add
            vp_add = visited_positions.add
            get_valid_slides_rec = self.get_valid_slides_rec

            for slide_direction in EnumUtils.Directions:
                slide_position = neighbour_at(slide_direction)

                if slide_position not in visited_positions and not has_piece_at(slide_position):
                    # Slide position is open
                    right = right_of(slide_direction)
                    left = left_of(slide_direction)

                    right_occupied = has_piece_at(neighbour_at(right))
                    left_occupied = has_piece_at(neighbour_at(left))

                    if right_occupied != left_occupied:  # Hive is not "tight"
                        # Can slide into slide position
                        move = Move(piece_name=target, position=slide_position)

                        old_len = valid_moves.count
                        vm_add(move)

                        if valid_moves.count > old_len:
                            # Sliding from this position has not been tested yet
                            vp_add(move.position)
                            get_valid_slides_rec(
                                target, slide_position, visited_positions, current_range + 1, valid_moves, max_range)

    def can_move_without_breaking_hive(self, target_piece):
        if target_piece.in_play and target_piece.position.stack == 0:
            # Try edge heuristic
            edges = 0
            last_has_piece = None

            for i in range(EnumUtils.NumDirections):
                neighbor = target_piece.position.neighbour_at(i)

                has_piece = self.has_piece_at(neighbor)
                if last_has_piece is not None:
                    if last_has_piece != has_piece:
                        edges += 1

                        if edges > 2:
                            break

                last_has_piece = has_piece

            if edges <= 2:
                return True

            # Temporarily remove piece from board
            original_position = target_piece.position
            self.move_piece(target_piece, None, False)

            # Determine if the hive is broken
            is_one_hive = self.is_one_hive()

            # Return piece to the board
            self.move_piece(target_piece, original_position, False)
            return is_one_hive

        return True

    # noinspection PyMethodMayBeStatic
    def placing_piece_in_order(self, target_piece):
        if target_piece.in_hand:
            try:
                return eval(piece_order_dict[target_piece.piece_name])
            except KeyError:
                pass
        return True

    def reset_caches(self):
        self._cached_valid_moves_by_piece = None
        self._cached_valid_placement_positions = None
        self._cached_enemy_queen_neighbors = None
        self.ValidMoveCacheResets += 1


piece_order_dict = {
    "WhiteSpider2": "self.get_piece(\"WhiteSpider1\").in_play",
    "WhiteBeetle2": "self.get_piece(\"WhiteBeetle1\").in_play",
    "WhiteGrasshopper2": "self.get_piece(\"WhiteGrasshopper1\").in_play",
    "WhiteGrasshopper3": "self.get_piece(\"WhiteGrasshopper2\").in_play",
    "WhiteSoldierAnt2": "self.get_piece(\"WhiteSoldierAnt1\").in_play",
    "WhiteSoldierAnt3": "self.get_piece(\"WhiteSoldierAnt2\").in_play",
    "BlackSpider2": "self.get_piece(\"BlackSpider1\").in_play",
    "BlackBeetle2": "self.get_piece(\"BlackBeetle1\").in_play",
    "BlackGrasshopper2": "self.get_piece(\"BlackGrasshopper1\").in_play",
    "BlackGrasshopper3": "self.get_piece(\"BlackGrasshopper2\").in_play",
    "BlackSoldierAnt2": "self.get_piece(\"BlackSoldierAnt1\").in_play",
    "BlackSoldierAnt3": "self.get_piece(\"BlackSoldierAnt2\").in_play",
}


class InvalidMoveException(Exception):
    def __init__(self, move, message=None):
        self.message = message
        
        if message:
            raise ValueError("%s: %s" % (move, message))
        raise ValueError("%s: %s" % (move, "You can't move that piece there."))
