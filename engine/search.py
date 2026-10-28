
from engine.legal_moves import (
    generate_legal_moves,
    make_move,
    undo_move,
    is_in_check,
)

from engine.evaluation import evaluate_position


INF = 10**9
MATE_SCORE = 100000
MATE_THRESHOLD = MATE_SCORE - 1000
MAX_TT_ENTRIES = 200000
MAX_PLY = 128

EXACT = 0
LOWER_BOUND = 1
UPPER_BOUND = 2

# Killer moves: two quiet cutoff moves per ply.
KILLER_MOVES = [[None, None] for _ in range(MAX_PLY)]

# History heuristic scores.
HISTORY_TABLE = {}


def position_key(board):
    """Create a hashable key for the current position."""
    return (
        tuple(board.board),
        board.turn,
        board.castling,
        board.en_passant,
        board.halfmove_clock,
    )


def _score_to_tt(score, ply):
    """Normalize mate scores before storing in TT."""
    if score >= MATE_THRESHOLD:
        return score + ply
    if score <= -MATE_THRESHOLD:
        return score - ply
    return score


def _score_from_tt(score, ply):
    """Restore mate scores from TT."""
    if score >= MATE_THRESHOLD:
        return score - ply
    if score <= -MATE_THRESHOLD:
        return score + ply
    return score


def _store_tt(tt, key, entry):
    """Store TT entry, preferring deeper searches."""
    if tt is None:
        return

    old_entry = tt.get(key)

    if old_entry is not None and old_entry["depth"] > entry["depth"]:
        return

    if len(tt) >= MAX_TT_ENTRIES and key not in tt:
        tt.clear()

    tt[key] = entry


def _is_capture(board, move):
    """Check whether a move captures a piece."""
    _, to_sq = move
    return board.board[to_sq] != "."


def _record_killer_move(move, ply):
    """Record a quiet move that caused a beta cutoff."""
    if ply >= MAX_PLY:
        return

    if move != KILLER_MOVES[ply][0]:
        KILLER_MOVES[ply][1] = KILLER_MOVES[ply][0]
        KILLER_MOVES[ply][0] = move


def _record_history_move(board, move, depth):
    """Increase history score for a successful quiet move."""
    key = (board.turn, move[0], move[1])
    HISTORY_TABLE[key] = HISTORY_TABLE.get(key, 0) + depth * depth

    if HISTORY_TABLE[key] > 100000:
        for history_key in HISTORY_TABLE:
            HISTORY_TABLE[history_key] //= 2


def order_moves(board, moves, tt_move=None, ply=0):
    """Order TT, captures, promotions, killer and history moves."""

    values = {
        "p": 100,
        "n": 320,
        "b": 330,
        "r": 500,
        "q": 900,
        "k": 20000,
    }

    killers = (
        KILLER_MOVES[ply]
        if ply < MAX_PLY
        else [None, None]
    )

    def move_priority(move):
        from_sq, to_sq = move
        attacker = board.board[from_sq]
        victim = board.board[to_sq]

        score = 0

        if move == tt_move:
            score += 10**7

        # MVV-LVA capture ordering.
        if victim != ".":
            score += (
                10 * values[victim.lower()]
                - values[attacker.lower()]
            )

        # Promotion bonus.
        if attacker.lower() == "p" and to_sq // 8 in (0, 7):
            score += 800

        # Killer and history heuristics for quiet moves.
        if victim == ".":
            if move == killers[0]:
                score += 9000
            elif move == killers[1]:
                score += 8000

            history_key = (board.turn, from_sq, to_sq)
            score += HISTORY_TABLE.get(history_key, 0)

        return score

    return sorted(moves, key=move_priority, reverse=True)


def minimax(
    board,
    depth,
    alpha,
    beta,
    maximizing,
    stats=None,
    tt=None,
    ply=0,
):
    """Alpha-beta minimax with TT, killer and history heuristics."""

    if stats is not None:
        stats["nodes"] = stats.get("nodes", 0) + 1

    original_alpha = alpha
    original_beta = beta

    key = position_key(board)
    tt_entry = tt.get(key) if tt is not None else None
    tt_move = None

    if tt_entry is not None:
        tt_move = tt_entry.get("best_move")

        if stats is not None:
            stats["tt_hits"] = stats.get("tt_hits", 0) + 1

        if tt_entry["depth"] >= depth:
            tt_score = _score_from_tt(tt_entry["score"], ply)
            flag = tt_entry["flag"]

            if flag == EXACT:
                return tt_score
            elif flag == LOWER_BOUND:
                alpha = max(alpha, tt_score)
            elif flag == UPPER_BOUND:
                beta = min(beta, tt_score)

            if alpha >= beta:
                return tt_score

    moves = generate_legal_moves(board)

    # Checkmate or stalemate.
    if not moves:
        if is_in_check(board, board.turn):
            score = (
                -MATE_SCORE + ply
                if board.turn == "w"
                else MATE_SCORE - ply
            )
        else:
            score = 0

        if tt is not None:
            _store_tt(
                tt,
                key,
                {
                    "depth": depth,
                    "score": _score_to_tt(score, ply),
                    "flag": EXACT,
                    "best_move": None,
                },
            )

        return score

    if depth <= 0:
        return evaluate_position(board)

    moves = order_moves(board, moves, tt_move, ply)

    best_move = None

    if maximizing:
        best_score = -INF

        for move in moves:
            old_state = make_move(board, move)

            try:
                score = minimax(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    False,
                    stats,
                    tt,
                    ply + 1,
                )
            finally:
                undo_move(board, move, old_state)

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, best_score)

            if alpha >= beta:
                if not _is_capture(board, move):
                    _record_killer_move(move, ply)
                    _record_history_move(board, move, depth)

                if stats is not None:
                    stats["cutoffs"] = stats.get("cutoffs", 0) + 1
                break

    else:
        best_score = INF

        for move in moves:
            old_state = make_move(board, move)

            try:
                score = minimax(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    True,
                    stats,
                    tt,
                    ply + 1,
                )
            finally:
                undo_move(board, move, old_state)

            if score < best_score:
                best_score = score
                best_move = move

            beta = min(beta, best_score)

            if alpha >= beta:
                if not _is_capture(board, move):
                    _record_killer_move(move, ply)
                    _record_history_move(board, move, depth)

                if stats is not None:
                    stats["cutoffs"] = stats.get("cutoffs", 0) + 1
                break

    if tt is not None:
        if best_score <= original_alpha:
            flag = UPPER_BOUND
        elif best_score >= original_beta:
            flag = LOWER_BOUND
        else:
            flag = EXACT

        _store_tt(
            tt,
            key,
            {
                "depth": depth,
                "score": _score_to_tt(best_score, ply),
                "flag": flag,
                "best_move": best_move,
            },
        )

    return best_score


def _search_root(board, moves, depth, stats, tt, pv_move=None):
    """Search every root move using iterative deepening."""

    maximizing = board.turn == "w"

    best_move = None
    best_score = -INF if maximizing else INF
    alpha = -INF
    beta = INF

    root_key = position_key(board)
    root_entry = tt.get(root_key)
    tt_move = root_entry.get("best_move") if root_entry else pv_move

    if pv_move is not None:
        tt_move = pv_move

    moves = order_moves(board, moves, tt_move, 0)

    for move in moves:
        old_state = make_move(board, move)

        try:
            score = minimax(
                board,
                depth - 1,
                alpha,
                beta,
                not maximizing,
                stats,
                tt,
                1,
            )
        finally:
            undo_move(board, move, old_state)

        if maximizing:
            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, best_score)

        else:
            if score < best_score:
                best_score = score
                best_move = move

            beta = min(beta, best_score)

    _store_tt(
        tt,
        root_key,
        {
            "depth": depth,
            "score": _score_to_tt(best_score, 0),
            "flag": EXACT,
            "best_move": best_move,
        },
    )

    return best_move, best_score


def find_best_move(board, depth=3, stats=None):
    """Iterative deepening with a shared transposition table."""

    if depth < 1:
        raise ValueError("Depth must be at least 1")

    moves = generate_legal_moves(board)

    if not moves:
        return None, None

    if stats is not None:
        stats["root_moves"] = len(moves)
        stats.setdefault("completed_depth", 0)
        stats.setdefault("tt_hits", 0)

    tt = {}
    best_move = None
    best_score = 0

    for current_depth in range(1, depth + 1):
        iteration_move, iteration_score = _search_root(
            board,
            moves,
            current_depth,
            stats,
            tt,
            best_move,
        )

        if iteration_move is not None:
            best_move = iteration_move
            best_score = iteration_score

        if stats is not None:
            stats["completed_depth"] = current_depth

    if stats is not None:
        stats["tt_entries"] = len(tt)

    return best_move, best_score
