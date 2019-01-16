import queue
from collections import deque

from MzingaShared.Core import Move as MoveCls, EnumUtils
from MzingaShared.Core.BoardMetrics import BoardMetrics
from MzingaShared.Core.CacheMetricsSet import CacheMetricsSet
from MzingaShared.Core.Move import Move
from MzingaShared.Core.MoveSet import MoveSet
from MzingaShared.Core.Piece import Piece
from MzingaShared.Core import Position as PositionCls
from MzingaShared.Core.Position import Position
from MzingaShared.Core.ZobristHash import ZobristHash
from MzingaShared.Core.EnumUtils import colours, colours_by_int, piece_names_by_int, piece_names, \
                                        EnumUtils as EnumUtilsCls, rings, directions

board_states = ["NotStarted", "InProgress", "Draw", "WhiteWins", "BlackWins"]


class Board:
    board_state = None
    game_type = None

    _board_metrics = None
    _current_turn = 0
    _zobrist_hash = None
    _pieces = []
    _pieces_by_position = {}
    _last_piece_moved = list(piece_names.keys())[0]  # "INVALID"

    # CACHES
    valid_move_cache_metrics_set = None
    valid_move_cache_resets = 0
    _cached_valid_moves_by_piece = None
    _cached_valid_placement_positions = None
    _visited_placements = set()
    _cached_enemy_queen_neighbours = None
    _cached_friendly_queen_neighbours = None
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
        return colours_by_int.get(self.current_turn % 2)

    @property
    def current_player_turn(self):
        return 1 + (self.current_turn // 2)

    @property
    def game_in_progress(self):
        return self.board_state in ["NotStarted", "InProgress"]

    @property
    def game_is_over(self):
        return self.board_state in ["WhiteWins", "BlackWins", "Draw"]

    @property
    def board_string(self):
        s = "%s%c" % (self.board_state, ';')
        s += "%s[%s]%c" % (self.current_turn_colour, self.current_player_turn, ';')

        for i in range(EnumUtils.num_piece_names):
            if self._pieces[i] is not None and self._pieces[i].in_play:
                s += "%s%c" % (self._pieces[i], ';')
        return s[:-1:]

    @property
    def zobrist_key(self):
        return self._zobrist_hash.value
    # END STATE PROPERTIES

    # PIECE ENUMERATION PROPERTIES
    @property
    def current_turn_pieces(self):
        is_white = self.current_turn_colour == "White"
        return EnumUtilsCls.white_piece_names() if is_white else EnumUtilsCls.black_piece_names()

    @property
    def pieces_in_play(self):
        return [piece_names_by_int.get(i) for i in range(EnumUtils.num_piece_names)
                if self._pieces[i] is not None and self._pieces[i].in_play]

    @property
    def white_hand(self):
        return [piece_names_by_int.get(i) for i in range(EnumUtils.num_piece_names // 2)
                if self._pieces[i] is not None and self._pieces[i].in_play]

    @property
    def black_hand(self):
        return [piece_names_by_int.get(i) for i in range(EnumUtils.num_piece_names // 2, EnumUtils.num_piece_names)
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
        self.board_state = "NotStarted"
        self.game_type = game_type

        self._board_metrics = BoardMetrics(game_type)
        self._current_turn = 0

        self._zobrist_hash = ZobristHash()
        self._pieces = []
        self._pieces_by_position = {}
        self._last_piece_moved = "INVALID"

        # CACHES
        self.valid_move_cache_metrics_set = CacheMetricsSet()
        self.valid_move_cache_resets = 0
        self._cached_valid_moves_by_piece = None
        self._cached_valid_placement_positions = None
        self._visited_placements = set()
        self._cached_enemy_queen_neighbours = None
        self._cached_friendly_queen_neighbours = None

    def __init__(self, board_string, game_type):
        self.init_state_vars(game_type)
        self.init_pieces()
        self.dummy_queen = Piece("WhiteQueenBee")

        # New game constructor
        if board_string == "START":
            return

        if board_string is None or board_string.isspace():
            raise ValueError("Invalid board_string.")

        # Board history string constructor:
        split = board_string.split(';')
        board_state_string = split[0]

        if board_state_string not in board_states:
            raise ValueError("%s%s" % ("Couldn't parse board state. ", board_string))

        self.board_state = board_state_string
        current_turn_split = list(filter(None, split[1].replace('[', ']').split(']')))
        current_turn_colour_string = current_turn_split[0]

        if current_turn_colour_string not in colours_by_int.values():
            raise ValueError("%s%s" % ("Couldn't parse current turn colour. ", board_string))

        current_player_turn_string = current_turn_split[1]
        self.current_turn = 2 * (int(current_player_turn_string) - 1) + colours[current_turn_colour_string]

        parsed_pieces = queue.Queue(EnumUtils.num_piece_names)
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

    def __repr__(self):
        return self.board_string

    def init_pieces(self):
        for i in range(EnumUtils.num_piece_names):
            self._pieces.append(Piece(EnumUtils.piece_names_by_int[i]))

    def has_piece_at(self, position):
        return self.get_piece(position) is not None

    def get_piece_position(self, piece_name):
        if piece_name == "INVALID":
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
            return self._pieces[piece_names[value]]

    def get_piece_on_top(self, value):
        if isinstance(value, Piece):
            while value.piece_above is not None:
                value = value.piece_above
            return value
        else:
            if value is None:
                raise ValueError("Invalid position.")
            value = self.get_piece_on_top_internal(value)
            return value.piece_name if value else list(piece_names.keys())[0]  # "INVALID"

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
                # self._pieces_by_position[piece.position] = None
                self._pieces_by_position.pop(piece.position)

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
        pieces_in_play = [p for p in self._pieces_by_position.values() if p is not None]
        pieces_visited, num_pieces = 1, len(pieces_in_play)  # pieces_visited == 1 to count 1st piece
        pieces_to_look_at = deque([pieces_in_play[0]])

        analyzed_pieces = set()
        get_piece = self.get_piece

        while len(pieces_to_look_at) > 0:
            current_piece = pieces_to_look_at.pop()
            n_at = current_piece.position.neighbour_at

            # Check all pieces at this stack level
            for i in range(EnumUtils.num_directions):
                neighbor_piece = get_piece(n_at(i))
                new = neighbor_piece not in analyzed_pieces and neighbor_piece not in pieces_to_look_at

                if neighbor_piece is not None and new:
                    pieces_to_look_at.append(neighbor_piece)
                    pieces_visited += 1

            # Check for all pieces above this one
            piece_above = current_piece.piece_above
            while piece_above is not None:
                pieces_visited += 1
                piece_above = piece_above.piece_above

            analyzed_pieces.add(current_piece)

        return pieces_visited == num_pieces

    # METRICS
    def get_board_metrics(self):
        self._board_metrics.reset()
        self._board_metrics.board_state = self.board_state

        # Get the metrics for the current turn
        self._set_current_player_metrics()

        # Save off current valid moves/placements since we'll be returning to it
        valid_moves_by_piece = self._cached_valid_moves_by_piece
        self._cached_valid_moves_by_piece = None

        valid_placement_positions = self._cached_valid_placement_positions
        self._cached_valid_placement_positions = None

        enemy_queen_neighbours = self._cached_enemy_queen_neighbours
        self._cached_enemy_queen_neighbours = None

        friendly_queen_neighbours = self._cached_friendly_queen_neighbours
        self._cached_friendly_queen_neighbours = None

        last_piece_moved = self._last_piece_moved
        self._last_piece_moved = list(piece_names.keys())[0]  # "INVALID"

        # Spoof going to the next turn to get the opponent's metrics
        self._current_turn += 1
        self._zobrist_hash.toggle_turn()
        self._set_current_player_metrics()
        self._current_turn -= 1
        self._zobrist_hash.toggle_turn()

        # Returned, so reload saved valid moves/placements into cache
        self._last_piece_moved = last_piece_moved
        self._cached_enemy_queen_neighbours = enemy_queen_neighbours
        self._cached_friendly_queen_neighbours = friendly_queen_neighbours
        self._cached_valid_placement_positions = valid_placement_positions
        self._cached_valid_moves_by_piece = valid_moves_by_piece

        return self._board_metrics

    def _set_current_player_metrics(self):
        # Optionally calculate extended board metrics:
        if self.game_type == "Extended":
            self.get_queen_metrics()
            self.get_board_ring_metrics()

        # Calculate piece metrics:
        for piece_name in self.current_turn_pieces:
            target_piece = self.get_piece(piece_name)
            p = self._board_metrics[piece_name]

            if target_piece is not None:
                if target_piece.in_play:
                    self._board_metrics.pieces_in_play += 1
                    p.in_play = 1
                else:
                    self._board_metrics.pieces_in_hand += 1
                    p.in_play = 0

                # Set noisy/quiet move, and ring metric counts:
                metric_counts = self.is_pinned(piece_name)
                is_pinned, p.noisy_move_count, p.quiet_move_count = metric_counts[0:3]
                if self.game_type == "Extended":
                    p.can_make_noisy_ring, p.can_make_defense_ring = metric_counts[3:]

                is_below = target_piece.in_play and target_piece.piece_above is not None
                p.is_pinned = 1 if is_pinned else 0
                p.is_covered = 1 if is_below else 0

                # Set neighbor counts
                total, p.friendly_neighbour_count, p.enemy_neighbour_count = self.count_neighbors(piece=target_piece)

    def is_pinned(self, piece_name):
        noisy_count, quiet_count = 0, 0
        can_make_noisy_ring, can_make_defense_ring = 0, 0
        is_pinned = True
        is_noisy_move, is_quiet_move = self.is_noisy_move, self.is_quiet_move
        makes_noisy_ring, makes_defense_ring = self.makes_noisy_ring, self.makes_defense_ring

        for move in self.get_valid_moves(piece_name):
            if move is None or move.is_pass:
                continue
            if move.piece_name == piece_name:
                is_pinned = False

            if is_noisy_move(move):
                noisy_count += 1
            else:
                if self.game_type == "Original":
                    quiet_count += 1
                else:
                    if is_quiet_move(piece_name, move):
                        quiet_count += 1

            # Optionally compute extended piece metrics:
            if self.game_type == "Extended":
                if can_make_noisy_ring != 1:
                    if makes_noisy_ring(move):
                        can_make_noisy_ring = 1

                if can_make_defense_ring != 1:
                    if makes_defense_ring(piece_name, move):
                        can_make_defense_ring = 1

        return is_pinned, noisy_count, quiet_count, can_make_noisy_ring, can_make_defense_ring

    def is_quiet_move(self, piece_name, move):
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
        # Determine enemy queen neighbours:
        if self._cached_enemy_queen_neighbours is None:
            self._cached_enemy_queen_neighbours = set()
            enemy_queen_name = "BlackQueenBee" if self.current_turn_colour == "White" else "WhiteQueenBee"
            enemy_queen_position = self.get_piece_position(enemy_queen_name)

            if enemy_queen_position is not None:
                # Add queen's neighboring positions
                add = self._cached_enemy_queen_neighbours.add
                neighbour_at = enemy_queen_position.neighbour_at

                for i in range(EnumUtils.num_directions):
                    add(neighbour_at(i))

        move_to_adjacent = move.position in self._cached_enemy_queen_neighbours
        piece_already_adjacent = self.get_piece_position(move.piece_name) in self._cached_enemy_queen_neighbours
        classically_noisy = move_to_adjacent and not piece_already_adjacent

        if self.game_type == "Original":
            return classically_noisy
        # Extended AI checks for moves which trap pieces into a space adjacent to the enemy queen:
        else:
            # Avoid extra work if the move is already noisy in the original sense:
            if classically_noisy:
                return classically_noisy

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
            newly_trapped_against_queen = \
                [p for p in newly_trapped if p.position in self._cached_enemy_queen_neighbours]
            return len(newly_trapped_against_queen) > 0

    def makes_noisy_ring(self, move):
        # Verify move position has at least two neighbours before checking for rings:
        move_occupied_neighbours = [move.position.neighbour_at(i) for i in EnumUtils.directions.values()
                                    if self.get_piece(move.position.neighbour_at(i)) is not None]
        if len(move_occupied_neighbours) < 2:
            return False

        origin = move.position
        piece_colour = move.piece_name[0:5]
        get_piece = self.get_piece

        def analyze_ring():
            ring_pieces = []
            referent = origin

            for angle in ring:
                referent = referent.neighbour_at(directions[angle])
                n = get_piece(referent)
                if n is None:
                    break
                if n.piece_name != move.piece_name:
                    ring_pieces.append(n.piece_name)

            # If the move makes a ring, check for queen bee presence and/or piece ratio:
            if len(ring_pieces) >= 5:
                white_pcs = 1 if piece_colour == "White" else 0
                black_pcs = 1 - white_pcs

                for piece_name in ring_pieces:
                    ring_piece_colour = piece_name[0:5]

                    if piece_name[-3:] == "Bee":
                        return ring_piece_colour == self.current_turn_colour
                    if ring_piece_colour == "White":
                        white_pcs += 1
                    else:
                        black_pcs += 1

                noisy_for_white = self.current_turn_colour == "White" and white_pcs > black_pcs
                noisy_for_black = self.current_turn_colour == "Black" and black_pcs > white_pcs
                if noisy_for_white or noisy_for_black:
                    return True
            return False

        # Check for 6pc rings in all directions:
        for ring in rings:
            makes_noisy_ring = analyze_ring()
            if makes_noisy_ring:
                return True

        # Check for 8pc rings in all directions:
        for ring in rings:
            ring = [ring[0], ring[0], ring[1], ring[2], ring[3], ring[3], ring[4]]
            makes_noisy_ring = analyze_ring()
            if makes_noisy_ring:
                return True

        return False

    def makes_defense_ring(self, piece_name, move):
        # Determine which set of positions to inspect:
        if piece_name[0:5] == self.current_turn_colour:
            queen_neighbour_set = self._cached_friendly_queen_neighbours
        else:
            queen_neighbour_set = self._cached_enemy_queen_neighbours

        if len(queen_neighbour_set) == 0:
            return False

        # Determine current number of non_sliding_neighbour_positions:
        tight_positions_1 = [p for p in queen_neighbour_set
                             if self.get_piece(p) is None and self.get_valid_slides_from_pos(p).count == 0]

        # Mock move, check again, then undo:
        piece = self.get_piece(piece_name)
        original_pos = piece.position
        self.move_piece(piece, move.position, update_zobrist=False)

        if piece_name[-3:] == "Bee":
            queen_neighbour_set = [move.position.neighbour_at(i) for i in EnumUtils.directions.values()]

        tight_positions_2 = [p for p in queen_neighbour_set
                             if self.get_piece(p) is None and self.get_valid_slides_from_pos(p).count == 0]
        self.move_piece(piece, original_pos, update_zobrist=False)

        # If a non-sliding-neighbour position was added to the friendly queen's neighbours, a defense ring was formed:
        if len(tight_positions_2) > len(tight_positions_1):
            return True
        return False

    def count_neighbors(self, piece_name=None, piece=None):
        if piece_name and not piece:
            return self.count_neighbors(piece=self.get_piece(piece_name))
        else:
            friendly_count = 0
            enemy_count = 0

            if piece.in_play:
                for i in range(EnumUtils.num_directions):
                    neighbor = self.get_piece(piece.position.neighbour_at(i))
                    if neighbor is not None:
                        if neighbor.colour == piece.colour:
                            friendly_count += 1
                        else:
                            enemy_count += 1

            return friendly_count + enemy_count, friendly_count, enemy_count

    def count_queen_neighbours(self, queen_position, colour):
        neighbour_count = 0
        non_sliding_neighbour_positions = 0
        friendly = self.current_turn_colour == colour

        if self._cached_friendly_queen_neighbours is None:
            self._cached_friendly_queen_neighbours = set()

        if queen_position is not None:
            neighbour_at = queen_position.neighbour_at
            fqn_add = self._cached_friendly_queen_neighbours.add

            for i in range(EnumUtils.num_directions):
                pos = neighbour_at(i)

                # Build friendly_queen_neighbours cache:
                if friendly:
                    fqn_add(pos)

                # Count occupied neighbouring spaces and check empty neighbours for tightness:
                if self.get_piece(pos) is not None:
                    neighbour_count += 1
                else:
                    valid_moves = self.get_valid_slides_from_pos(pos)
                    if valid_moves.count == 0:
                        non_sliding_neighbour_positions += 1

        return 6 - neighbour_count, non_sliding_neighbour_positions

    def check_pos_neighbours(self, pos, neighbour_bees):
        n_white, n_black, n_count = 0, 0, 0
        empty_n = None

        # Check for neighbours in each direction:
        for d in range(EnumUtils.num_directions):
            neighbour_i_pos = pos.neighbour_at(d)
            piece_at_dir_i = self.get_piece(neighbour_i_pos)

            if piece_at_dir_i is not None:
                if piece_at_dir_i.colour == "White":
                    n_white += 1
                else:
                    n_black += 1

                if piece_at_dir_i.piece_name[-3::] == "Bee":
                    neighbour_bees.add(piece_at_dir_i.colour)

                n_count += 1
            else:
                empty_n = neighbour_i_pos

        return n_white, n_black, n_count, empty_n

    def get_board_ring_metrics(self):
        bm = self._board_metrics
        bm.black_noisy_ring = 0
        bm.white_noisy_ring = 0
        empty_positions = set()

        # Find all empty positions:
        for piece in self._pieces_by_position.values():
            if piece is None or piece.in_hand:
                continue

            neighbour_at = piece.position.neighbour_at
            if bm[piece.piece_name].is_pinned == 1:
                continue

            for i in range(EnumUtils.num_directions):
                pos = neighbour_at(i)
                if self.get_piece(pos) is None:
                    empty_positions.add(pos)

        # Filter candidates to find ring centres:
        for pos in empty_positions:
            neighbour_bees = set()
            n_white, n_black, n_count, empty_n = self.check_pos_neighbours(pos, neighbour_bees)

            # If exactly one neighbour is open, check for 8pc rings:
            if n_count == 5:
                n_white_2, n_black_2, n_count_2, _ = self.check_pos_neighbours(empty_n, neighbour_bees)

                if n_count_2 == 5:
                    n_white += n_white_2
                    n_black += n_black_2
                    n_count = 6

            # Pos is a ring centre:
            if n_count == 6:
                if n_black > n_white:
                    bm.black_noisy_ring += 1
                elif n_black < n_white:
                    bm.white_noisy_ring += 1
                else:
                    bm.black_noisy_ring += 1
                    bm.white_noisy_ring += 1

                # Additionally increment counter if bees are included in the ring:
                for bee_colour in neighbour_bees:
                    if bee_colour == "White":
                        bm.white_noisy_ring += 1
                    else:
                        bm.black_noisy_ring += 1

    def get_queen_metrics(self):
        white_queen_position = self.get_piece_position("WhiteQueenBee")
        black_queen_position = self.get_piece_position("BlackQueenBee")

        wq_metrics = self.count_queen_neighbours(white_queen_position, "White")
        self._board_metrics.white_queen_life, self._board_metrics.white_queen_tight_spaces = wq_metrics

        bq_metrics = self.count_queen_neighbours(black_queen_position, "Black")
        self._board_metrics.black_queen_life, self._board_metrics.black_queen_tight_spaces = bq_metrics

    def get_trapped_neighbours(self, position, enemies_only=False):
        trapped_neighbours = []
        for i in range(EnumUtils.num_directions):
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
                self._cached_valid_moves_by_piece = MoveSet(size=EnumUtils.num_piece_names)

            piece_name_index = piece_names[piece_name]
            cached = self._cached_valid_moves_by_piece[piece_name_index]
            null_entry = False

            if isinstance(cached, Move):
                null_entry = cached.is_pass
            if isinstance(cached, MoveSet):
                null_entry = cached.count == 0

            if cached is not None and not null_entry:
                # MoveSet is cached in L1 cache
                self.valid_move_cache_metrics_set["ValidMoves." + EnumUtilsCls.get_short_name(piece_name)].hit()
            else:
                # MoveSet is not cached in L1 cache
                self.valid_move_cache_metrics_set["ValidMoves." + EnumUtilsCls.get_short_name(piece_name)].miss()

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

                    for i in range(EnumUtils.num_directions):
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

        if self._cached_valid_placement_positions is None or len(self._cached_valid_placement_positions) == 0:
            self._cached_valid_placement_positions = set()
            self._visited_placements.clear()

            for i in range(EnumUtils.num_piece_names):
                piece = self._pieces[i]

                valid_piece = piece is not None and piece.in_play

                # Piece is in play, on the top and is the right color, look through neighbors
                if valid_piece and self.piece_is_on_top(piece) and piece.colour == target_colour:
                    bottom_position = self.get_piece_on_bottom(piece).position
                    self._visited_placements.add(bottom_position)

                    for j in range(EnumUtils.num_directions):
                        neighbor = bottom_position.neighbour_at(j)

                        # Neighboring position is a potential, verify its neighbors are empty or same color
                        old_len = len(self._visited_placements)
                        self._visited_placements.add(neighbor)

                        if len(self._visited_placements) > old_len and not self.has_piece_at(neighbor):
                            valid_placement = True
                            for k in range(EnumUtils.num_directions):
                                surrounding_position = neighbor.neighbour_at(k)
                                surrounding_piece = self.get_piece_on_top_internal(surrounding_position)

                                if surrounding_piece is not None and surrounding_piece.colour != target_colour:
                                    valid_placement = False
                                    break

                            if valid_placement:
                                self._cached_valid_placement_positions.add(neighbor)

            self.valid_move_cache_metrics_set["ValidPlacements"].miss()
        else:
            self.valid_move_cache_metrics_set["ValidPlacements"].hit()

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
        for direction in EnumUtils.directions.keys():
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

        for direction in EnumUtils.directions:
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

    def get_valid_slides(self, target_piece, max_range=None, dummy=False):
        valid_moves = MoveSet()
        starting_position = target_piece.position

        visited_positions = set()
        visited_positions.add(starting_position)
        piece_name = target_piece.piece_name

        # Avoid invoking self.move_piece when checking dummy_queen slides:
        if dummy:
            target_piece.move(None)
            self.get_valid_slides_rec(piece_name, starting_position, visited_positions, 0, valid_moves, max_range)
            target_piece.move(starting_position)
        else:
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

            for slide_direction in EnumUtils.directions:
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

    def get_valid_slides_from_pos(self, pos):
        # Use dummy queen to check a position for 'tightness':
        self.dummy_queen.move(pos)
        valid_moves = self.get_valid_slides(self.dummy_queen, 1, dummy=True)
        self.dummy_queen.move(None)
        return valid_moves

    def can_move_without_breaking_hive(self, target_piece):
        if target_piece.in_play and target_piece.position.stack == 0:
            # Try edge heuristic
            edges = 0
            last_has_piece = None

            neighbour_at = target_piece.position.neighbour_at
            has_piece_at = self.has_piece_at

            for i in range(EnumUtils.num_directions):
                has_piece = has_piece_at(neighbour_at(i))

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
        self._cached_enemy_queen_neighbours = None
        self._cached_friendly_queen_neighbours = None
        self.valid_move_cache_resets += 1


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
