import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chess_lstm.inference import predict_candidate_moves
from chess_lstm.model import load_model
from chess_lstm.tokenizer import ChessTokenizer
from engine.board import ChessBoard
from engine.fen import load_fen
from engine.legal_moves import generate_legal_moves, make_move
from engine.san import san_to_move


ROOT = Path(__file__).resolve().parents[1]
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
MODEL_PATH = ROOT / "chess_lstm" / "chess_model.keras"
TOKENIZER_PATH = ROOT / "dataset" / "processed" / "chess_tokenizer.json"


def test_saved_model_predictions_are_legal():
    model = load_model(MODEL_PATH)
    tokenizer = ChessTokenizer.load(TOKENIZER_PATH)
    board = ChessBoard()
    load_fen(board, STARTING_FEN)

    history = ["e4", "e5"]
    sequence_length = model.input_shape[1]
    assert model.output_shape[-1] == tokenizer.vocabulary_size

    for san in history:
        make_move(board, san_to_move(board, san))

    encoded_history = tokenizer.encode(history)
    model_input = np.asarray(
        [[0] * (sequence_length - len(encoded_history)) + encoded_history],
        dtype=np.int32,
    )
    probabilities = model.predict(model_input, verbose=0)[0]
    print("Raw top-10 predictions:")
    for token_id in probabilities.argsort()[::-1][:10]:
        san = tokenizer.decode([int(token_id)])[0]
        print(f"  id={int(token_id)} san={san} probability={probabilities[token_id]:.6f}")

    candidates = predict_candidate_moves(
        board,
        history,
        model,
        tokenizer,
        sequence_length=sequence_length,
        top_k=5,
    )

    print("Predicted SAN candidates:")
    for san, move, probability in candidates:
        print(f"  {san}: {probability:.6f}")
        assert move in generate_legal_moves(board)

    if not candidates:
        print("No legal candidates were returned.")
    assert candidates, "Expected at least one legal candidate for the aligned position"

    assert predict_candidate_moves(
        board,
        history,
        model,
        tokenizer,
        sequence_length=sequence_length,
        top_k=0,
    ) == []


if __name__ == "__main__":
    test_saved_model_predictions_are_legal()
    print("CHESS INFERENCE TEST PASSED!")
