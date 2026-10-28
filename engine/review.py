
import json
import math
import traceback

from sqlalchemy.orm import Session

from database.connection import SessionLocal
from database.models import Game, MoveRecord, GameReview

from engine.board import ChessBoard
from engine.fen import load_fen
from engine.evaluation import evaluate_position
from engine.legal_moves import generate_legal_moves, make_move, undo_move
from engine.search import minimax, INF


REVIEW_DEPTH = 1


def move_to_uci(board, move):
    return (
        board.index_to_square(move[0])
        + board.index_to_square(move[1])
    )


def classify_move(cpl):
    if cpl <= 10:
        return "BEST"
    elif cpl <= 25:
        return "GREAT"
    elif cpl <= 50:
        return "GOOD"
    elif cpl <= 100:
        return "INACCURACY"
    elif cpl <= 200:
        return "MISTAKE"
    return "BLUNDER"


def calculate_accuracy(cpl_values):
    if not cpl_values:
        return 100.0

    scores = [
        100.0 * math.exp(-max(0, cpl) / 120.0)
        for cpl in cpl_values
    ]

    return round(sum(scores) / len(scores), 2)


def analyze_position(fen_before, played_uci):
    board = ChessBoard()
    load_fen(board, fen_before)

    legal_moves = generate_legal_moves(board)

    if not legal_moves:
        return None

    white_to_move = board.turn == "w"

    candidates = []

    for move in legal_moves:
        uci = move_to_uci(board, move)

        old_state = make_move(board, move)

        try:
            score = minimax(
                board,
                REVIEW_DEPTH,
                -INF,
                INF,
                board.turn == "w",
                stats={},
                tt={},
                ply=1,
            )
        finally:
            undo_move(board, move, old_state)

        candidates.append({
            "uci": uci,
            "score": score,
        })

    if white_to_move:
        best = max(candidates, key=lambda item: item["score"])
    else:
        best = min(candidates, key=lambda item: item["score"])

    played = next(
        (item for item in candidates if item["uci"] == played_uci),
        None,
    )

    if played is None:
        return None

    if white_to_move:
        cpl = best["score"] - played["score"]
    else:
        cpl = played["score"] - best["score"]

    cpl = max(0, cpl)

    return {
        "best_move": best["uci"],
        "best_eval": best["score"],
        "played_eval": played["score"],
        "centipawn_loss": round(cpl, 2),
        "quality": classify_move(cpl),
    }


def generate_game_review(game_id: int):
    db: Session = SessionLocal()

    try:
        review = (
            db.query(GameReview)
            .filter(GameReview.game_id == game_id)
            .first()
        )

        if review is None:
            review = GameReview(
                game_id=game_id,
                status="pending",
            )
            db.add(review)
            db.commit()
            db.refresh(review)

        if review.status == "completed":
            return

        review.status = "analyzing"
        review.error = None
        db.commit()

        records = (
            db.query(MoveRecord)
            .filter(MoveRecord.game_id == game_id)
            .order_by(MoveRecord.ply.asc())
            .all()
        )

        if not records:
            raise ValueError("No recorded moves found for this game.")

        annotations = []
        white_losses = []
        black_losses = []

        for record in records:
            analysis = analyze_position(
                record.fen_before,
                record.uci,
            )

            if analysis is None:
                continue

            if record.color.lower() in ("white", "w"):
                white_losses.append(analysis["centipawn_loss"])
            else:
                black_losses.append(analysis["centipawn_loss"])

            annotations.append({
                "ply": record.ply,
                "move_number": record.move_number,
                "color": record.color,
                "san": record.san,
                "uci": record.uci,
                "fen_before": record.fen_before,
                "fen_after": record.fen_after,
                "eval_before": record.eval_before,
                "eval_after": record.eval_after,
                **analysis,
            })

        result = {
            "game_id": game_id,
            "engine": "FORMULON custom Minimax evaluator",
            "review_depth": REVIEW_DEPTH,
            "annotations": annotations,
            "move_count": len(annotations),
            "accuracy_note": (
                "Accuracy and move classifications are approximate "
                "and based on the custom engine evaluator."
            ),
        }

        review.review_json = json.dumps(result)
        review.white_accuracy = calculate_accuracy(white_losses)
        review.black_accuracy = calculate_accuracy(black_losses)
        review.opening_name = "Not identified"
        review.status = "completed"
        review.error = None
        db.commit()

    except Exception as exc:
        db.rollback()

        review = (
            db.query(GameReview)
            .filter(GameReview.game_id == game_id)
            .first()
        )

        if review:
            review.status = "failed"
            review.error = str(exc)
            db.commit()

        traceback.print_exc()

    finally:
        db.close()
