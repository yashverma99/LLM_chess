import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chess_lstm.dataset import build_training_examples, load_pgn_games
from chess_lstm.inference import predict_candidate_moves
from chess_lstm.model import create_model, load_model
from chess_lstm.tokenizer import ChessTokenizer
from engine.board import ChessBoard
from engine.fen import load_fen


ROOT = Path(__file__).resolve().parents[1]
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_tokenizer_and_sample_preprocessing(tmp_path):
    games = load_pgn_games(ROOT / "dataset" / "raw" / "sample.pgn")
    inputs, labels, tokenizer, sequence_length = build_training_examples(games)
    assert len(games) == 1
    assert len(games[0]) == 10
    assert inputs.shape == (9, sequence_length)
    assert labels.shape == (9,)

    path = tmp_path / "tokenizer.json"
    tokenizer.save(path)
    restored = ChessTokenizer.load(path)
    assert restored.encode(["e4", "e5"]) == tokenizer.encode(["e4", "e5"])


class FixedPredictionModel:
    def __init__(self, probabilities):
        self.probabilities = np.asarray([probabilities], dtype=np.float32)

    def predict(self, inputs, verbose=0):
        return self.probabilities


def test_prediction_returns_only_legal_moves():
    tokenizer = ChessTokenizer().fit([["e4", "e5", "Nf3"]])
    probabilities = [0.0] * tokenizer.vocabulary_size
    probabilities[tokenizer.token_to_id["e5"]] = 0.9
    probabilities[tokenizer.token_to_id["e4"]] = 0.8
    model = FixedPredictionModel(probabilities)
    board = ChessBoard()
    load_fen(board, STARTING_FEN)

    candidates = predict_candidate_moves(
        board, [], model, tokenizer, sequence_length=3, top_k=2
    )
    assert [candidate[0] for candidate in candidates] == ["e4", "Nf3"]


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("tensorflow") is None,
    reason="TensorFlow is not installed",
)
def test_training_and_model_loading(tmp_path):
    games = load_pgn_games(ROOT / "dataset" / "raw" / "sample.pgn")
    inputs, labels, tokenizer, sequence_length = build_training_examples(games)
    model = create_model(tokenizer.vocabulary_size, sequence_length, lstm_units=8)
    model.fit(inputs, labels, epochs=1, batch_size=4, verbose=0)
    model_path = tmp_path / "model.keras"
    tokenizer_path = tmp_path / "tokenizer.json"
    model.save(model_path)
    tokenizer.save(tokenizer_path)
    assert load_model(model_path).output_shape[-1] == tokenizer.vocabulary_size
    assert ChessTokenizer.load(tokenizer_path).vocabulary_size == tokenizer.vocabulary_size
