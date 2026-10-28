
BOARD_SIZE = 8

KNIGHT_OFFSETS = [
    (-2, -1), (-2, 1),
    (-1, -2), (-1, 2),
    (1, -2), (1, 2),
    (2, -1), (2, 1)
]

KING_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

BISHOP_DIRECTIONS = [
    (-1, -1), (-1, 1),
    (1, -1), (1, 1)
]

ROOK_DIRECTIONS = [
    (-1, 0), (1, 0),
    (0, -1), (0, 1)
]


def is_inside(row, col):
    return 0 <= row < 8 and 0 <= col < 8


def get_color(piece):
    if piece == ".":
        return None

    return "w" if piece.isupper() else "b"


def add_move(moves, board, from_index, row, col):

    if not is_inside(row, col):
        return False

    to_index = row * 8 + col
    target = board.board[to_index]

    moving_piece = board.board[from_index]

    if target == ".":
        moves.append((from_index, to_index))
        return True

    if get_color(target) != get_color(moving_piece):
        moves.append((from_index, to_index))

    return False


def generate_pawn_moves(board, index):

    moves = []

    row, col = divmod(index, 8)
    piece = board.board[index]
    color = get_color(piece)

    direction = -1 if color == "w" else 1
    start_row = 6 if color == "w" else 1

    # One square forward
    next_row = row + direction

    if is_inside(next_row, col):
        next_index = next_row * 8 + col

        if board.board[next_index] == ".":
            moves.append((index, next_index))

            # Two squares forward
            if row == start_row:
                two_row = row + 2 * direction
                two_index = two_row * 8 + col

                if board.board[two_index] == ".":
                    moves.append((index, two_index))

    # Diagonal captures
    for dc in (-1, 1):

        new_row = row + direction
        new_col = col + dc

        if not is_inside(new_row, new_col):
            continue

        target_index = new_row * 8 + new_col
        target = board.board[target_index]

        if target != "." and get_color(target) != color:
            moves.append((index, target_index))

        # En passant
        target_square = board.index_to_square(target_index)

        if board.en_passant == target_square:
            moves.append((index, target_index))

    return moves


def generate_knight_moves(board, index):

    moves = []
    row, col = divmod(index, 8)

    for dr, dc in KNIGHT_OFFSETS:
        add_move(moves, board, index, row + dr, col + dc)

    return moves


def generate_sliding_moves(board, index, directions):

    moves = []
    row, col = divmod(index, 8)

    for dr, dc in directions:

        new_row = row + dr
        new_col = col + dc

        while is_inside(new_row, new_col):

            can_continue = add_move(
                moves, board, index, new_row, new_col
            )

            if not can_continue:
                break

            new_row += dr
            new_col += dc

    return moves


def generate_king_moves(board, index):

    moves = []
    row, col = divmod(index, 8)

    for dr, dc in KING_OFFSETS:
        add_move(moves, board, index, row + dr, col + dc)

    return moves


def generate_piece_moves(board, index):

    piece = board.board[index]

    if piece == ".":
        return []

    piece_type = piece.lower()

    if piece_type == "p":
        return generate_pawn_moves(board, index)

    if piece_type == "n":
        return generate_knight_moves(board, index)

    if piece_type == "b":
        return generate_sliding_moves(
            board, index, BISHOP_DIRECTIONS
        )

    if piece_type == "r":
        return generate_sliding_moves(
            board, index, ROOK_DIRECTIONS
        )

    if piece_type == "q":
        return generate_sliding_moves(
            board, index,
            BISHOP_DIRECTIONS + ROOK_DIRECTIONS
        )

    if piece_type == "k":
        return generate_king_moves(board, index)

    return []


def generate_all_moves(board, color=None):

    if color is None:
        color = board.turn

    moves = []

    for index, piece in enumerate(board.board):

        if piece == ".":
            continue

        if get_color(piece) == color:
            moves.extend(generate_piece_moves(board, index))

    return moves
