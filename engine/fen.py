
from engine.board import ChessBoard


def load_fen(board, fen):
    parts = fen.split()

    if len(parts) != 6:
        raise ValueError("Invalid FEN")

    position, turn, castling, en_passant, halfmove, fullmove = parts

    rows = position.split("/")

    if len(rows) != 8:
        raise ValueError("FEN must contain 8 rows")

    new_board = []

    for row in rows:
        count = 0

        for char in row:
            if char.isdigit():
                empty = int(char)

                if not 1 <= empty <= 8:
                    raise ValueError("Invalid empty square count")

                new_board.extend(["."] * empty)
                count += empty

            elif char in "prnbqkPRNBQK":
                new_board.append(char)
                count += 1

            else:
                raise ValueError("Invalid piece")

        if count != 8:
            raise ValueError("Each row must contain 8 squares")

    if turn not in ("w", "b"):
        raise ValueError("Invalid active color")

    if castling != "-" and (
        any(c not in "KQkq" for c in castling)
        or len(set(castling)) != len(castling)
    ):
        raise ValueError("Invalid castling rights")

    if en_passant != "-":
        if (
            len(en_passant) != 2
            or en_passant[0] not in "abcdefgh"
            or en_passant[1] not in "36"
        ):
            raise ValueError("Invalid en passant square")

    try:
        halfmove_clock = int(halfmove)
        fullmove_number = int(fullmove)
    except ValueError:
        raise ValueError("Invalid move counters")

    if halfmove_clock < 0 or fullmove_number < 1:
        raise ValueError("Invalid move counters")

    board.board = new_board
    board.turn = turn
    board.castling = castling
    board.en_passant = en_passant
    board.halfmove_clock = halfmove_clock
    board.fullmove_number = fullmove_number

    # Reset repetition history to the loaded position.
    board.position_history = [to_fen(board)]


def to_fen(board):
    rows = []

    for row in range(8):
        result = ""
        empty = 0

        for col in range(8):
            piece = board.board[row * 8 + col]

            if piece == ".":
                empty += 1
            else:
                if empty:
                    result += str(empty)
                    empty = 0

                result += piece

        if empty:
            result += str(empty)

        rows.append(result)

    position = "/".join(rows)

    return (
        position + " "
        + board.turn + " "
        + board.castling + " "
        + board.en_passant + " "
        + str(board.halfmove_clock) + " "
        + str(board.fullmove_number)
    )
