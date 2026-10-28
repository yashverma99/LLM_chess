
from pathlib import Path
from functools import lru_cache

from engine.legal_moves import (
    generate_legal_moves,
    make_move,
    undo_move,
)
from engine.search import (
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

    remaining = order_moves(board, remaining, tt_move, ply)

    for priority_move in (pv_move, tt_move):
        if priority_move is None or priority_move not in legal_moves:
            continue

        if priority_move in candidate_moves:
            candidate_moves.remove(priority_move)

        if priority_move in remaining:
            remaining.remove(priority_move)

        candidate_moves.insert(0, priority_move)

    return candidate_moves + remaining


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
    LSTM-guided move ordering with automatic Minimax fallback.
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

    try:
        lstm_model, lstm_tokenizer = _load_lstm(
            model,
            tokenizer,
            model_path,
            tokenizer_path,
        )

        from chess_lstm.inference import predict_candidate_moves

        candidates = predict_candidate_moves(
            board,
            history or [],
            lstm_model,
            lstm_tokenizer,
            lstm_model.input_shape[1],
            top_k=top_k,
        )

        stats["mode"] = (
            "lstm-guided" if candidates else "engine-fallback"
        )

    except Exception as error:
        stats["lstm_error"] = str(error)
        best_move, score = find_best_move(board, depth, stats)
        stats["searched_moves"] = len(legal_moves)
        stats["mode"] = "engine-fallback"
        return best_move, score, stats

    stats["lstm_candidates"] = len(candidates)

    best_move = None
    best_score = float("-inf")
    pv_move = None

    for current_depth in range(1, depth + 1):
        alpha = float("-inf")
        beta = float("inf")

        key = position_key(board)
        tt_move = None

        ordered_moves = _ordered_legal_moves(
            board,
            legal_moves,
            candidates,
            tt_move,
            pv_move,
            0,
        )

        iteration_best_move = None
        iteration_best_score = float("-inf")

        for move in ordered_moves:
            undo_data = make_move(board, move)

            try:
                score = -_hybrid_minimax(
                    board,
                    current_depth - 1,
                    -beta,
                    -alpha,
                    1,
                    stats,
                )
            finally:
                undo_move(board, move, undo_data)

            stats["root_searched"] += 1

            if score > iteration_best_score:
                iteration_best_score = score
                iteration_best_move = move

            alpha = max(alpha, score)

        if iteration_best_move is not None:
            best_move = iteration_best_move
            best_score = iteration_best_score
            pv_move = best_move
            stats["completed_depth"] = current_depth

    stats["searched_moves"] = stats["root_searched"]

    return best_move, best_score, stats


def _hybrid_minimax(
    board,
    depth,
    alpha,
    beta,
    ply,
    stats,
):
    stats["nodes"] += 1

    if depth <= 0:
        return find_best_move(board, 1, stats)[1]

    legal_moves = generate_legal_moves(board)

    if not legal_moves:
        return 0

    moves = order_moves(board, legal_moves, None, ply)

    best_score = float("-inf")

    for move in moves:
        undo_data = make_move(board, move)

        try:
            score = -_hybrid_minimax(
                board,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
                stats,
            )
        finally:
            undo_move(board, move, undo_data)

        if score > best_score:
            best_score = score

        alpha = max(alpha, score)

        if alpha >= beta:
            stats["cutoffs"] += 1

            if not _is_capture(board, move):
                _record_killer_move(move, ply)
                _record_history_move(board,move, depth)

            break

    return best_score
