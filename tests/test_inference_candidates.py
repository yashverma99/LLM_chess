import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chess_lstm.inference import predict_candidate_moves
from chess_lstm.tokenizer import ChessTokenizer
from engine.board import ChessBoard
from engine.fen import load_fen
from engine.legal_moves import generate_legal_moves


STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class FixedPredictionModel:
    def __init__(self, probabilities):
        self.probabilities = np.asarray([probabilities], dtype=np.float32)

    def predict(self, inputs, verbose=0):
        return self.probabilities


def starting_board():
    board = ChessBoard()
    load_fen(board, STARTING_FEN)
    return board


def test_illegal_high_probability_tokens_do_not_fill_top_k():
    tokenizer = ChessTokenizer().fit([["e5", "Nf3", "e4"]])
    probabilities = [0.0] * tokenizer.vocabulary_size
    probabilities[tokenizer.token_to_id["e5"]] = 0.99
    probabilities[tokenizer.token_to_id["Nf3"]] = 0.80
    probabilities[tokenizer.token_to_id["e4"]] = 0.70

    candidates = predict_candidate_moves(
        starting_board(),
        [],
        FixedPredictionModel(probabilities),
        tokenizer,
        sequence_length=3,
        top_k=2,
    )

    assert [candidate[0] for candidate in candidates] == ["Nf3", "e4"]


def test_all_returned_moves_are_legal_and_probability_ordered():
    tokenizer = ChessTokenizer().fit([["e4", "Nf3", "e5"]])
    probabilities = [0.0] * tokenizer.vocabulary_size
    probabilities[tokenizer.token_to_id["e4"]] = 0.40
    probabilities[tokenizer.token_to_id["Nf3"]] = 0.90
    probabilities[tokenizer.token_to_id["e5"]] = 0.01
    board = starting_board()

    candidates = predict_candidate_moves(
        board,
        [],
        FixedPredictionModel(probabilities),
        tokenizer,
        sequence_length=3,
        top_k=2,
    )

    legal_moves = set(generate_legal_moves(board))
    assert len(candidates) == 2
    assert all(move in legal_moves for _, move, _ in candidates)
    assert [candidate[0] for candidate in candidates] == ["Nf3", "e4"]
    assert candidates[0][2] >= candidates[1][2]


def test_no_legal_candidates_returns_empty_list():
    tokenizer = ChessTokenizer().fit([["e5"]])
    probabilities = [0.0] * tokenizer.vocabulary_size
    probabilities[tokenizer.token_to_id["e5"]] = 1.0

    assert predict_candidate_moves(
        starting_board(),
        [],
        FixedPredictionModel(probabilities),
        tokenizer,
        sequence_length=3,
        top_k=3,
    ) == []
