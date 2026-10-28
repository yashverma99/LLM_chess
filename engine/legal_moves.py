
from engine.moves import (
    generate_all_moves,
    get_color,
    is_inside
)


# --------------------------------
# 1. Find King
# --------------------------------

def find_king(board, color):

    king = "K" if color == "w" else "k"

    for index, piece in enumerate(board.board):
        if piece == king:
            return index

    raise ValueError("King not found")


# --------------------------------
# 2. Check Square Attacked
# --------------------------------

def is_square_attacked(board, square, by_color):

    target_row, target_col = divmod(square, 8)

    for index, piece in enumerate(board.board):

        if piece == "." or get_color(piece) != by_color:
            continue

        row, col = divmod(index, 8)
        piece_type = piece.lower()

        # Pawn attacks
        if piece_type == "p":

            direction = -1 if by_color == "w" else 1

            for dc in (-1, 1):

                r = row + direction
                c = col + dc

                if (r, c) == (target_row, target_col):
                    return True

        # Knight attacks
        elif piece_type == "n":

            offsets = [
                (-2, -1), (-2, 1),
                (-1, -2), (-1, 2),
                (1, -2), (1, 2),
                (2, -1), (2, 1)
            ]

            for dr, dc in offsets:

                if (row + dr, col + dc) == (
                    target_row, target_col
                ):
                    return True

        # King attacks
        elif piece_type == "k":

            if max(
                abs(row - target_row),
                abs(col - target_col)
            ) == 1:
                return True

        # Sliding pieces
        elif piece_type in ("b", "r", "q"):

            dr = target_row - row
            dc = target_col - col

            if piece_type == "b" and abs(dr) != abs(dc):
                continue

            if piece_type == "r" and not (dr == 0 or dc == 0):
                continue

            if piece_type == "q" and not (
                dr == 0 or dc == 0 or abs(dr) == abs(dc)
            ):
                continue

            step_row = (dr > 0) - (dr < 0)
            step_col = (dc > 0) - (dc < 0)

            r = row + step_row
            c = col + step_col

            blocked = False

            while (r, c) != (target_row, target_col):

                if board.board[r * 8 + c] != ".":
                    blocked = True
                    break

                r += step_row
                c += step_col

            if not blocked:
                return True

    return False


# --------------------------------
# 3. Check Detection
# --------------------------------

def is_in_check(board, color):

    king_square = find_king(board, color)

    enemy = "b" if color == "w" else "w"

    return is_square_attacked(
        board,
        king_square,
        enemy
    )


# --------------------------------
# 4. Castling Moves
# --------------------------------

def generate_castling_moves(board, color):

    moves = []

    if color == "w":

        king_square = 60
        enemy = "b"

        if board.board[60] != "K":
            return moves

        if is_in_check(board, "w"):
            return moves

        # Kingside
        if (
            "K" in board.castling
            and board.board[61] == "."
            and board.board[62] == "."
            and board.board[63] == "R"
            and not is_square_attacked(board, 61, enemy)
            and not is_square_attacked(board, 62, enemy)
        ):
            moves.append((60, 62))

        # Queenside
        if (
            "Q" in board.castling
            and board.board[59] == "."
            and board.board[58] == "."
            and board.board[57] == "."
            and board.board[56] == "R"
            and not is_square_attacked(board, 59, enemy)
            and not is_square_attacked(board, 58, enemy)
        ):
            moves.append((60, 58))

    else:

        king_square = 4
        enemy = "w"

        if board.board[4] != "k":
            return moves

        if is_in_check(board, "b"):
            return moves

        # Kingside
        if (
            "k" in board.castling
            and board.board[5] == "."
            and board.board[6] == "."
            and board.board[7] == "r"
            and not is_square_attacked(board, 5, enemy)
            and not is_square_attacked(board, 6, enemy)
        ):
            moves.append((4, 6))

        # Queenside
        if (
            "q" in board.castling
            and board.board[3] == "."
            and board.board[2] == "."
            and board.board[1] == "."
            and board.board[0] == "r"
            and not is_square_attacked(board, 3, enemy)
            and not is_square_attacked(board, 2, enemy)
        ):
            moves.append((4, 2))

    return moves


# --------------------------------
# 5. Update Castling Rights
# --------------------------------

def update_castling_rights(board, from_sq, to_sq, moving_piece):

    rights = board.castling

    if moving_piece == "K":
        rights = rights.replace("K", "").replace("Q", "")

    elif moving_piece == "k":
        rights = rights.replace("k", "").replace("q", "")

    rook_squares = {
        63: "K",
        56: "Q",
        7: "k",
        0: "q"
    }

    if from_sq in rook_squares:
        rights = rights.replace(rook_squares[from_sq], "")

    if to_sq in rook_squares:
        rights = rights.replace(rook_squares[to_sq], "")

    board.castling = rights if rights else "-"


# --------------------------------
# 6. Make Move
# --------------------------------

def make_move(board, move):

    from_sq, to_sq = move

    moving_piece = board.board[from_sq]
    captured_piece = board.board[to_sq]

    if moving_piece == ".":
        raise ValueError("No piece at source square")

    color = get_color(moving_piece)

    old_state = {
        "turn": board.turn,
        "castling": board.castling,
        "en_passant": board.en_passant,
        "halfmove_clock": board.halfmove_clock,
        "fullmove_number": board.fullmove_number,
        "captured_piece": captured_piece,
        "moving_piece": moving_piece,
        "en_passant_capture": None,
        "rook_move": None
    }

    # En passant capture
    if (
        moving_piece.lower() == "p"
        and to_sq == board.square_to_index(board.en_passant)
        if board.en_passant != "-"
        else False
    ):

        captured_sq = to_sq + (8 if color == "w" else -8)

        old_state["en_passant_capture"] = (
            captured_sq,
            board.board[captured_sq]
        )

        board.board[captured_sq] = "."

    # Move piece
    board.board[to_sq] = moving_piece
    board.board[from_sq] = "."

    # Castling: move rook
    if moving_piece.lower() == "k" and abs(to_sq - from_sq) == 2:

        if to_sq > from_sq:
            rook_from = from_sq + 3
            rook_to = from_sq + 1
        else:
            rook_from = from_sq - 4
            rook_to = from_sq - 1

        rook_piece = board.board[rook_from]

        old_state["rook_move"] = (
            rook_from,
            rook_to,
            rook_piece
        )

        board.board[rook_to] = rook_piece
        board.board[rook_from] = "."

    # Pawn promotion: automatically promote to queen
    if moving_piece == "P" and to_sq // 8 == 0:
        board.board[to_sq] = "Q"

    elif moving_piece == "p" and to_sq // 8 == 7:
        board.board[to_sq] = "q"

    # Update castling rights
    update_castling_rights(
        board, from_sq, to_sq, moving_piece
    )

    # Update en passant target
    board.en_passant = "-"

    if moving_piece.lower() == "p" and abs(to_sq - from_sq) == 16:
        middle_sq = (from_sq + to_sq) // 2
        board.en_passant = board.index_to_square(middle_sq)

    # Update move counters
    if moving_piece.lower() == "p" or captured_piece != ".":
        board.halfmove_clock = 0
    else:
        board.halfmove_clock += 1

    if color == "b":
        board.fullmove_number += 1

    board.turn = "b" if color == "w" else "w"

    # Add current position to history for threefold repetition detection
    from engine.fen import to_fen
    board.position_history.append(to_fen(board))

    return old_state


# --------------------------------
# 7. Undo Move
# --------------------------------

def undo_move(board, move, old_state):
    from_sq, to_sq = move

    # Remove the last position from history when undoing
    if board.position_history:
        board.position_history.pop()

    board.turn = old_state["turn"]
    board.castling = old_state["castling"]
    board.en_passant = old_state["en_passant"]
    board.halfmove_clock = old_state["halfmove_clock"]
    board.fullmove_number = old_state["fullmove_number"]

    moving_piece = old_state["moving_piece"]

    board.board[from_sq] = moving_piece
    board.board[to_sq] = old_state["captured_piece"]

    # Undo en passant
    if old_state["en_passant_capture"] is not None:

        captured_sq, captured_piece = old_state["en_passant_capture"]

        board.board[captured_sq] = captured_piece

    # Undo castling rook move
    if old_state["rook_move"] is not None:

        rook_from, rook_to, rook_piece = old_state["rook_move"]

        board.board[rook_from] = rook_piece
        board.board[rook_to] = "."


# --------------------------------
# 8. Generate Legal Moves
# --------------------------------

def generate_legal_moves(board, color=None):

    if color is None:
        color = board.turn

    if color not in ("w", "b"):
        raise ValueError("Invalid color")

    pseudo_moves = generate_all_moves(board, color)

    # Add castling moves
    pseudo_moves.extend(
        generate_castling_moves(board, color)
    )

    legal_moves = []

    for move in pseudo_moves:

        old_state = make_move(board, move)

        try:
            if not is_in_check(board, color):
                legal_moves.append(move)

        finally:
            undo_move(board, move, old_state)

    return legal_moves