hash_part_by_turn_colour = None
hash_part_by_last_moved_piece = None
hash_part_by_position = None

def rand_64(next):
    return next * 1103515245 + 12345

def init(zh, unique_positions, int num_piece_names):
    zh.Value = 0

    # Only compute hash tables once:
    global hash_part_by_turn_colour, hash_part_by_last_moved_piece, hash_part_by_position
    if hash_part_by_turn_colour is None:
        zh._next = rand_64(zh._next)
        zh._hashPartByTurnColor = zh._next

        zh._hashPartByLastMovedPiece = [0] * num_piece_names
        zh._hashPartByPosition = {}

        for i in range(num_piece_names):
            zh._next = rand_64(zh._next)
            zh._hashPartByLastMovedPiece[i] = zh._next

        for i in range(num_piece_names):
            zh._hashPartByPosition[i] = {}

            for pos in unique_positions:
                zh._next = rand_64(zh._next)
                zh._hashPartByPosition[i][pos] = zh._next

        hash_part_by_turn_colour = zh._hashPartByTurnColor
        hash_part_by_last_moved_piece = zh._hashPartByLastMovedPiece
        hash_part_by_position = zh._hashPartByPosition
    else:
        zh._hashPartByTurnColor = hash_part_by_turn_colour
        zh._hashPartByLastMovedPiece = hash_part_by_last_moved_piece
        zh._hashPartByPosition = hash_part_by_position