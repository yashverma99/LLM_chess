import re

from engine.legal_moves import (
    generate_legal_moves,
    is_in_check,
    make_move,
    undo_move,
)


_SAN_PATTERN = re.compile(
    r"^(?P<piece>[KQRBN])?"
    r"(?P<disambiguation>[a-h1-8]{0,2})"
    r"(?P<capture>x)?"
    r"(?P<destination>[a-h][1-8])"
    r"(?P<promotion>=[QRBN])?"
    r"(?P<suffix>[+#])?$"
)


def _validate_suffix(board, move, suffix):
    if suffix is None:
        return

    old_state = make_move(board, move)
    try:
        opponent = board.turn
        in_check = is_in_check(board, opponent)
        has_legal_reply = bool(generate_legal_moves(board))

        if suffix == "+" and (not in_check or not has_legal_reply):
            raise ValueError("SAN check suffix does not match the resulting position")

        if suffix == "#" and (not in_check or has_legal_reply):
            raise ValueError(
                "SAN checkmate suffix does not match the resulting position"
            )
    finally:
        undo_move(board, move, old_state)


def san_to_move(board, san):
    """Convert a SAN move into the engine's ``(from_index, to_index)`` format."""

    if not isinstance(san, str):
        raise ValueError("SAN move must be a string")

    text = san.strip().replace("0-0-0", "O-O-O").replace("0-0", "O-O")
    if not text:
        raise ValueError("SAN move cannot be empty")

    legal_moves = generate_legal_moves(board)

    castle_match = re.fullmatch(r"(O-O-O|O-O)([+#])?", text)
    if castle_match:
        castle, suffix = castle_match.groups()
        target = (
            58 if board.turn == "w" else 2
        ) if castle == "O-O-O" else (
            62 if board.turn == "w" else 6
        )
        king_source = 60 if board.turn == "w" else 4
        candidates = [
            move
            for move in legal_moves
            if move == (king_source, target)
        ]
        if len(candidates) != 1:
            raise ValueError(f"Illegal or ambiguous SAN move: {san!r}")
        _validate_suffix(board, candidates[0], suffix)
        return candidates[0]

    match = _SAN_PATTERN.fullmatch(text)
    if match is None:
        raise ValueError(f"Invalid SAN: {san!r}")

    piece_symbol = match.group("piece") or "P"
    disambiguation = match.group("disambiguation")
    is_capture = match.group("capture") is not None
    destination = match.group("destination")
    promotion = match.group("promotion")
    suffix = match.group("suffix")

    if promotion is not None and promotion != "=Q":
        raise ValueError("Engine currently supports queen promotion only")

    if piece_symbol == "P" and len(disambiguation) > 1:
        raise ValueError(f"Invalid pawn disambiguation in SAN: {san!r}")

    if piece_symbol == "P" and is_capture and (
        len(disambiguation) != 1 or disambiguation not in "abcdefgh"
    ):
        raise ValueError(f"Invalid pawn capture in SAN: {san!r}")

    if piece_symbol != "P" and len(disambiguation) == 2:
        if disambiguation[0] not in "abcdefgh" or disambiguation[1] not in "12345678":
            raise ValueError(f"Invalid disambiguation in SAN: {san!r}")

    to_sq = board.square_to_index(destination)
    candidates = []

    for move in legal_moves:
        from_sq, target_sq = move
        if target_sq != to_sq:
            continue

        piece = board.board[from_sq]
        if piece.lower() != piece_symbol.lower():
            continue

        source = board.index_to_square(from_sq)
        if len(disambiguation) == 1 and disambiguation not in source:
            continue
        if len(disambiguation) == 2 and source != disambiguation:
            continue

        actual_capture = board.board[to_sq] != "."
        if piece_symbol == "P" and board.en_passant == destination:
            actual_capture = True
        if actual_capture != is_capture:
            continue

        reaches_last_rank = piece_symbol == "P" and destination[1] in "18"
        if reaches_last_rank != (promotion is not None):
            continue
        candidates.append(move)

    if len(candidates) != 1:
        raise ValueError(f"Illegal or ambiguous SAN move: {san!r}")

    _validate_suffix(board, candidates[0], suffix)
    return candidates[0]


def move_to_san(board, move):
    """Convert the engine's ``(from_index, to_index)`` move format into a SAN string."""
    from_sq, to_sq = move
    piece = board.board[from_sq]
    
    if piece == '.':
        raise ValueError("No piece at source square")
    
    # Handle castling
    if piece.lower() == 'k':
        # King-side castling (O-O)
        if abs(to_sq - from_sq) == 2:
            if to_sq > from_sq:  # King moves from e1 to g1 (60 -> 62) or e8 to g8 (4->6)
                old_state = make_move(board, move)
                if is_in_check(board, board.turn):
                    undo_move(board, move, old_state)
                    return "O-O#" if is_in_check(board, "w" if board.turn == "b" else "b") and not bool(generate_legal_moves(board)) else "O-O"
                undo_move(board, move, old_state)
                return "O-O"
            else:  # Queen-side castling (O-O-O)
                old_state = make_move(board, move)
                if is_in_check(board, board.turn):
                    undo_move(board, move, old_state)
                    return "O-O-O#" if is_in_check(board, "w" if board.turn == "b" else "b") and not bool(generate_legal_moves(board)) else "O-O-O"
                undo_move(board, move, old_state)
                return "O-O-O"
    
    # Regular piece move
    piece_symbol = piece.upper()
    if piece_symbol == 'P':
        piece_symbol = ''
    
    from_square = board.index_to_square(from_sq)
    to_square = board.index_to_square(to_sq)
    
    # Check for captures
    is_capture = board.board[to_sq] != '.'
    if board.en_passant == to_square and piece.lower() == 'p':
        is_capture = True
    
    capture_symbol = 'x' if is_capture else ''
    
    # Handle disambiguation
    legal_moves = generate_legal_moves(board)
    same_pieces = []
    for m in legal_moves:
        m_from, m_to = m
        if m_to == to_sq and board.board[m_from] == piece:
            same_pieces.append(m)
    
    disambiguation = ''
    if len(same_pieces) > 1:
        # Need to disambiguate
        files = set()
        ranks = set()
        for m in same_pieces:
            mf, _ = m
            ms = board.index_to_square(mf)
            files.add(ms[0])
            ranks.add(ms[1])
        from_file = from_square[0]
        from_rank = from_square[1]
        if len(files) > 1:
            disambiguation += from_file
        if len(ranks) > 1:
            disambiguation += from_rank
        if len(files) == 1 and len(ranks) == 1:
            disambiguation = from_file + from_rank
    
    # Pawn captures need file disambiguation
    if piece.lower() == 'p' and is_capture:
        disambiguation = from_square[0]
    
    # Build SAN string
    san = f"{piece_symbol}{disambiguation}{capture_symbol}{to_square}"
    
    # Check for promotion
    if piece.lower() == 'p' and (to_square[1] in ('1', '8')):
        san += "=Q"  # Always queen promotion
    
    # Add check/checkmate suffix
    old_state = make_move(board, move)
    opponent_turn = board.turn
    in_check = is_in_check(board, opponent_turn)
    has_legal_moves = bool(generate_legal_moves(board))
    undo_move(board, move, old_state)
    
    if in_check and not has_legal_moves:
        san += "#"
    elif in_check:
        san += "+"
    
    return san