
from engine.moves import get_color, is_inside
from engine.legal_moves import is_square_attacked, find_king


# Piece values in centipawns
PIECE_VALUES = {
    "p": 100,
    "n": 320,
    "b": 330,
    "r": 500,
    "q": 900,
    "k": 20000
}

# Important center squares
CENTER_SQUARES = [27, 28, 35, 36]


def evaluate_material(board):
    """Calculate material advantage."""

    score = 0

    for piece in board.board:

        if piece == ".":
            continue

        value = PIECE_VALUES[piece.lower()]

        if piece.isupper():
            score += value
        else:
            score -= value

    return score


def evaluate_piece_position(board):
    """Reward useful piece positioning and development."""

    score = 0

    for index, piece in enumerate(board.board):

        if piece == "." or piece.lower() == "k":
            continue

        row, col = divmod(index, 8)

        # Distance from the center
        center_distance = (
            abs(row - 3.5) + abs(col - 3.5)
        )

        centralization = int((7 - center_distance) * 4)

        # Reward pawn advancement
        if piece.lower() == "p":

            advancement = (
                6 - row if piece.isupper()
                else row - 1
            )

            positional_value = advancement * 5

        elif piece.lower() in ("n", "b"):

            positional_value = centralization * 2

        elif piece.lower() == "q":

            positional_value = centralization

        else:
            positional_value = 0

        if piece.isupper():
            score += positional_value
        else:
            score -= positional_value

    return score


def evaluate_pawn_structure(board):
    """Evaluate doubled, isolated and passed pawns."""

    score = 0

    white_pawns = []
    black_pawns = []

    for index, piece in enumerate(board.board):

        if piece == "P":
            white_pawns.append(index)

        elif piece == "p":
            black_pawns.append(index)

    white_files = [0] * 8
    black_files = [0] * 8

    for index in white_pawns:
        white_files[index % 8] += 1

    for index in black_pawns:
        black_files[index % 8] += 1

    # Doubled pawns
    for count in white_files:
        if count > 1:
            score -= 20 * (count - 1)

    for count in black_files:
        if count > 1:
            score += 20 * (count - 1)

    # Isolated and passed pawns
    for index in white_pawns:

        row, col = divmod(index, 8)

        # Isolated pawn
        has_neighbor = any(
            white_files[c] > 0
            for c in (col - 1, col + 1)
            if 0 <= c < 8
        )

        if not has_neighbor:
            score -= 15

        # Passed pawn: no opposing pawn ahead
        blocked_by_enemy = False

        for enemy_index in black_pawns:

            enemy_row, enemy_col = divmod(enemy_index, 8)

            if (
                abs(enemy_col - col) <= 1
                and enemy_row < row
            ):
                blocked_by_enemy = True
                break

        if not blocked_by_enemy:
            score += (7 - row) * 15

    for index in black_pawns:

        row, col = divmod(index, 8)

        has_neighbor = any(
            black_files[c] > 0
            for c in (col - 1, col + 1)
            if 0 <= c < 8
        )

        if not has_neighbor:
            score += 15

        blocked_by_enemy = False

        for enemy_index in white_pawns:

            enemy_row, enemy_col = divmod(enemy_index, 8)

            if (
                abs(enemy_col - col) <= 1
                and enemy_row > row
            ):
                blocked_by_enemy = True
                break

        if not blocked_by_enemy:
            score -= row * 15

    return score


def evaluate_center_control(board):
    """Reward control of the four central squares."""

    score = 0

    for square in CENTER_SQUARES:

        if is_square_attacked(board, square, "w"):
            score += 15

        if is_square_attacked(board, square, "b"):
            score -= 15

        piece = board.board[square]

        if piece == "P":
            score += 10

        elif piece == "p":
            score -= 10

    return score


def evaluate_king_safety(board):
    """Evaluate king shelter and attacks near the king."""

    score = 0

    for color in ("w", "b"):

        king_square = find_king(board, color)

        row, col = divmod(king_square, 8)

        friendly_pawn = "P" if color == "w" else "p"
        enemy_color = "b" if color == "w" else "w"

        direction = -1 if color == "w" else 1

        # Pawn shield
        shield = 0

        for dc in (-1, 0, 1):

            r = row + direction
            c = col + dc

            if is_inside(r, c):

                if board.board[r * 8 + c] == friendly_pawn:
                    shield += 1

        safety_score = shield * 12

        # Enemy attacks around the king
        danger = 0

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):

                r = row + dr
                c = col + dc

                if is_inside(r, c):

                    square = r * 8 + c

                    if is_square_attacked(
                        board, square, enemy_color
                    ):
                        danger += 1

        safety_score -= danger * 10

        if color == "w":
            score += safety_score
        else:
            score -= safety_score

    return score


def evaluate_position(board):
    """
    Return a position score from White's perspective.
    Positive = White advantage.
    Negative = Black advantage.
    """

    return (
        evaluate_material(board)
        + evaluate_piece_position(board)
        + evaluate_pawn_structure(board)
        + evaluate_center_control(board)
        + evaluate_king_safety(board)
    )
