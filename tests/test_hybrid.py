import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chess_lstm.tokenizer import ChessTokenizer
from engine.board import ChessBoard
from engine.fen import load_fen, to_fen
from engine.hybrid import select_move
from engine.legal_moves import generate_legal_moves
from engine.search import find_best_move


STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class FixedModel:
    def __init__(self, probabilities):
        self.probabilities = probabilities
        self.input_shape = (None, 9)

    def predict(self, inputs, verbose=0):
        return [self.probabilities]


def starting_board():
    board = ChessBoard()
    load_fen(board, STARTING_FEN)
    return board


def test_lstm_guided_search_uses_only_legal_moves_and_preserves_board():
    board = starting_board()
    original_fen = to_fen(board)
    tokenizer = ChessTokenizer().fit([["e4", "e5", "Nf3"]])
    probabilities = [0.0] * tokenizer.vocabulary_size
    probabilities[tokenizer.token_to_id["e4"]] = 1.0

    move, score, stats = select_move(
        board,
        history=[],
        depth=1,
        model=FixedModel(probabilities),
        tokenizer=tokenizer,
        top_k=3,
    )

    assert move in generate_legal_moves(board)
    assert isinstance(score, int)
    assert stats["mode"] == "lstm-guided"
    assert stats["searched_moves"] == stats["legal_moves"]
    assert to_fen(board) == original_fen


def test_missing_lstm_files_fall_back_to_engine_search():
    board = starting_board()
    original_fen = to_fen(board)
    expected_move, expected_score = find_best_move(board, depth=1)

    move, score, stats = select_move(
        board,
        depth=1,
        model_path=Path("missing-model.keras"),
        tokenizer_path=Path("missing-tokenizer.json"),
    )

    assert (move, score) == (expected_move, expected_score)
    assert stats["mode"] == "engine-fallback"
    assert "lstm_error" in stats
    assert to_fen(board) == original_fen


def test_empty_lstm_predictions_fall_back_to_engine_search():
    board = starting_board()
    tokenizer = ChessTokenizer()
    probabilities = [0.0] * tokenizer.vocabulary_size

    move, score, stats = select_move(
        board,
        depth=1,
        model=FixedModel(probabilities),
        tokenizer=tokenizer,
    )

    assert move in generate_legal_moves(board)
    assert isinstance(score, int)
    assert stats["mode"] == "engine-fallback"
