from MzingaShared.Core import Position
from MzingaShared.Core.Move import Move
from MzingaShared.Core.Piece import Piece
from MzingaShared.Core.MoveSet import MoveSet
from MzingaShared.Core.EnumUtils import EnumUtils
from MzingaShared.Core.EnumUtils import directions

boardspace_pass = "pass"


def parse_move_string(board, move_string) -> Move:
    if board is None:
        raise ValueError("board cannot be None")
    if move_string is None or move_string.isspace():
        raise ValueError("move_string cannot be None")

    move_string = move_string.strip()

    try:
        # Attempt to parse as an algebraic move
        return Move(move_string=move_string)
    except ValueError:
        pass

    move_string_parts = list(filter(None, move_string.split(' ')))
    moving_piece = EnumUtils.parse_short_name(move_string_parts[0])

    if board.board_state == "NotStarted":
        # First move is on the origin
        return Move(moving_piece, Position.origin)

    target_string = move_string_parts[1].replace('-', '').replace('/', '').replace('\\', '')
    target_piece = EnumUtils.parse_short_name(target_string)
    separator_idx = index_of_any(move_string_parts[1], ['-', '/', '\\'])

    if separator_idx < 0:
        # Putting a piece on top of another
        return Move(moving_piece, board.get_piece_position(target_piece).get_above())

    separator = move_string_parts[1][separator_idx]
    target_position = board.get_piece_position(target_piece)

    if separator_idx == 0:
        # Moving piece on the left-hand side of the target piece
        if separator == '-':
            return Move(moving_piece, target_position.neighbour_at(directions["UpLeft"]))
        elif separator == '/':
            return Move(moving_piece, target_position.neighbour_at(directions["DownLeft"]))
        elif separator == '\\':
            return Move(moving_piece, target_position.neighbour_at(directions["Up"]))

    elif separator_idx == len(target_string):
        # Moving piece on the right-hand side of the target piece
        if separator == '-':
            return Move(moving_piece, target_position.neighbour_at(directions["DownRight"]))
        elif separator == '/':
            return Move(moving_piece, target_position.neighbour_at(directions["UpRight"]))
        elif separator == '\\':
            return Move(moving_piece, target_position.neighbour_at(directions["Down"]))
    return None


def to_boardspace_move_string(board, move):
    if board is None:
        raise ValueError("board cannot be None")
    if move is None:
        raise ValueError("move_string cannot be None")
    if move.is_pass:
        return boardspace_pass
    if move.colour != board.current_turn_colour:
        return None

    start_piece = to_boardspace_piece_name(move.piece_name)

    if board.current_turn == 0:
        return start_piece
    else:
        end_piece = ""

    if move.position.stack > 0:
        # On top of board
        piece_below = board.get_piece_internal(move.position.get_below())
        end_piece = to_boardspace_piece_name(piece_below.piece_name)
    else:
        # Find neighbor to move.Position
        for d in directions.values():
            pos = move.position.neighbour_at(d)
            neighbor = board.get_piece_on_top(pos)

            if neighbor == move.piece_name:
                pos_below = board.get_piece_position(neighbor).get_below()
                neighbor = board.get_piece_internal(pos_below) if pos_below is not None else "INVALID"

            if neighbor is not None and neighbor != "INVALID":
                if isinstance(neighbor, Piece):
                    end_piece = to_boardspace_piece_name(neighbor.piece_name)
                else:
                    end_piece = to_boardspace_piece_name(neighbor)

                if d == directions["Up"]:
                    end_piece += "\\"
                elif d == directions["UpRight"]:
                    end_piece = "/" + end_piece
                elif d == directions["DownRight"]:
                    end_piece = "-" + end_piece
                elif d == directions["Down"]:
                    end_piece = "\\" + end_piece
                elif d == directions["DownLeft"]:
                    end_piece += "/"
                elif d == directions["UpLeft"]:
                    end_piece += "-"
                break

    return start_piece if end_piece.isspace() else "%s %s" % (start_piece, end_piece)


def try_normalize_boardspace_move_string(move_string):
    try:
        normalized_move_string = normalize_boardspace_move_string(move_string)
        return True, normalized_move_string
    except ValueError or Exception:
        return False, None


def normalize_boardspace_move_string(move_string):
    if move_string is None or move_string.isspace():
        raise ValueError("Invalid move_string.")

    move_string_parts = list(filter(None, move_string.split(' ')))
    moving_piece = EnumUtils.parse_short_name(move_string_parts[0])

    if len(move_string_parts) == 1:
        return to_boardspace_piece_name(moving_piece)

    target_string = move_string_parts[1].replace('-', '').replace('/', '').replace('\\', '') 
    separator_idx = index_of_any(move_string_parts[1], ['-', '/', '\\'])
    target_piece = EnumUtils.parse_short_name(target_string)

    if separator_idx < 0:
        return "%s %s" % (to_boardspace_piece_name(moving_piece), to_boardspace_piece_name(target_piece))

    separator = move_string_parts[1][separator_idx]

    if separator_idx == 0:
        # Moving piece on the left - hand side of the target piece
        return "%s %c%s" % (to_boardspace_piece_name(moving_piece), separator, to_boardspace_piece_name(target_piece))
    elif separator_idx == len(target_string):
        # Moving piece on the right - hand side of the target piece
        return "%s %s%c" % (to_boardspace_piece_name(moving_piece), to_boardspace_piece_name(target_piece), separator)
    return None


def parse_move_string_list(board, move_string_list):
    if board is None:
        raise ValueError("board cannot be None.")
    if move_string_list is None or move_string_list.isspace():
        raise ValueError("Invalid move_string_list.")

    split = move_string_list.split(';')
    moves = MoveSet()

    for i in split:
        moves.add(parse_move_string(board, split[i]))
    return moves


def to_boardspace_move_string_list(board, moves):
    if board is None:
        raise ValueError("board cannot be None.")
    if moves is None:
        raise ValueError("moves cannot be None.")

    return "".join(["%s%c" % (to_boardspace_move_string(board, m), ';') for m in moves])[0:-1]


def to_boardspace_piece_name(piece_name):
    name = EnumUtils.get_short_name(piece_name)

    if name is not None and len(name) > 0:
        name = name[0].lower() + name[1:]
    return name


def index_of_any(string, char_list):
    indices = [string.find(c) for c in char_list if c in string]
    return min(indices) if indices else -1
