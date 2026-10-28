
from pathlib import Path
from functools import lru_cache

from chess_lstm.inference import predict_candidate_moves
from engine.legal_moves import (
    generate_legal_moves,
    make_move,
    undo_move,
)
from engine.search import (
    INF,
    minimax,
    find_best_move,
    order_moves,
    position_key,
    _store_tt,
    _score_to_tt,
    _is_capture,
    _record_killer_move,
    _record_history_move,
)


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "chess_lstm"
    / "chess_model.keras"
)

DEFAULT_TOKENIZER_PATH = (
    Path(__file__).resolve().parents[1]
    / "dataset"
    / "processed"
    / "chess_tokenizer.json"
)


@lru_cache(maxsize=1)
def _load_default_lstm():
    from chess_lstm.model import load_model
    from chess_lstm.tokenizer import ChessTokenizer

    model = load_model(DEFAULT_MODEL_PATH)
    tokenizer = ChessTokenizer.load(DEFAULT_TOKENIZER_PATH)

    return model, tokenizer


def warmup_lstm():
    return _load_default_lstm()


def _load_lstm(
    model=None,
    tokenizer=None,
    model_path=None,
    tokenizer_path=None,
):
    if model is not None and tokenizer is not None:
        return model, tokenizer

    if model_path is None and tokenizer_path is None:
        return _load_default_lstm()

    from chess_lstm.model import load_model
    from chess_lstm.tokenizer import ChessTokenizer

    return (
        load_model(model_path or DEFAULT_MODEL_PATH),
        ChessTokenizer.load(tokenizer_path or DEFAULT_TOKENIZER_PATH),
    )


def _ordered_legal_moves(
    board,
    legal_moves,
    candidates,
    tt_move=None,
    pv_move=None,
    ply=0,
):
    candidate_moves = []

    for candidate in candidates:
        if not isinstance(candidate, (tuple, list)) or len(candidate) < 2:
            continue

        try:
            move = tuple(candidate[1])
        except TypeError:
            continue

        if (
            len(move) == 2
            and move in legal_moves
            and move not in candidate_moves
        ):
            candidate_moves.append(move)

    remaining = [
        move for move in legal_moves
        if move not in candidate_moves
    ]

    remaining = order_moves(
        board,
        remaining,
        tt_move,
        ply,
    )

    # TT and previous iteration move get highest priority.
    for priority_move in (pv_move, tt_move):
        if priority_move is None or priority_move not in legal_moves:
            continue

        if priority_move in candidate_moves:
            candidate_moves.remove(priority_move)

        if priority_move in remaining:
            remaining.remove(priority_move)

        if priority_move not in candidate_moves:
            candidate_moves.insert(0, priority_move)

    return candidate_moves + remaining


def _search_ordered_moves(
    board,
    moves,
    depth,
    stats=None,
    tt=None,
):
    maximizing = board.turn == "w"

    best_move = None
    best_score = -INF if maximizing else INF

    alpha = -INF
    beta = INF

    for move in moves:
        if stats is not None:
            stats["root_searched"] = (
                stats.get("root_searched", 0) + 1
            )

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
                best_move = move
                best_score = score

            alpha = max(alpha, best_score)

        else:
            if score < best_score:
                best_move = move
                best_score = score

            beta = min(beta, best_score)

    return best_move, best_score


def select_move(
    board,
    history=None,
    depth=3,
    model=None,
    tokenizer=None,
    model_path=None,
    tokenizer_path=None,
    top_k=5,
):
    """
    LSTM-guided root move ordering with:
    - Iterative deepening
    - Transposition table
    - Killer move heuristic
    - History heuristic
    - Alpha-beta minimax
    """

    if depth < 1:
        raise ValueError("Depth must be at least 1")

    legal_moves = generate_legal_moves(board)

    stats = {
        "depth": depth,
        "completed_depth": 0,
        "legal_moves": len(legal_moves),
        "searched_moves": 0,
        "lstm_candidates": 0,
        "mode": "engine-fallback",
        "nodes": 0,
        "cutoffs": 0,
        "root_searched": 0,
        "tt_hits": 0,
    }

    if not legal_moves:
        return None, None, stats

    candidates = []
    lstm_error = None

    try:
        lstm_model, lstm_tokenizer = _load_lstm(
            model,
            tokenizer,
            model_path,
            tokenizer_path,
        )

        sequence_length = lstm_model.input_shape[1]

        candidates = predict_candidate_moves(
            board,
            history or [],
            lstm_model,
            lstm_tokenizer,
            sequence_length,
            top_k=top_k,
        )

        stats["mode"] = (
            "lstm-guided" if candidates else "engine-fallback"
        )

    except (
        ImportError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        lstm_error = str(error)

    if lstm_error:
        stats["lstm_error"] = lstm_error

        best_move, score = find_best_move(
            board,
            depth,
            stats,
        )

        stats["searched_moves"] = len(legal_moves)
        stats["mode"] = "engine-fallback"

        return best_move, score, stats

    stats["lstm_candidates"] = len({
        tuple(candidate[1])
        for candidate in candidates
        if isinstance(candidate, (tuple, list))
        and len(candidate) >= 2
    })

    tt = {}

    best_move = None
    best_score = -INF if board.turn == "w" else INF

    for current_depth in range(1, depth + 1):
        root_key = position_key(board)

        root_entry = tt.get(root_key)
        tt_move = (
            root_entry.get("best_move")
            if root_entry else None
        )

        ordered_moves = _ordered_legal_moves(
            board,
            legal_moves,
            candidates,
            tt_move,
            best_move,
            0,
        )

        stats["searched_moves"] = len(ordered_moves)

        iteration_move, iteration_score = _search_ordered_moves(
            board,
            ordered_moves,
            current_depth,
            stats,
            tt,
        )

        if iteration_move is not None:
            best_move = iteration_move
            best_score = iteration_score

        stats["completed_depth"] = current_depth

        _store_tt(
            tt,
            root_key,
            {
                "depth": current_depth,
                "score": _score_to_tt(best_score, 0),
                "flag": 0,
                "best_move": best_move,
            },
        )

    stats["tt_entries"] = len(tt)

    return best_move, best_score, stats


find_hybrid_move = select_move
