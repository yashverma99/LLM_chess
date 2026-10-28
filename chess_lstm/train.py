import argparse
from pathlib import Path

import numpy as np

from .dataset import build_training_examples, load_pgn_games
from .model import create_model


def train(pgn_path, model_path, tokenizer_path, epochs=10, batch_size=32):
    games = load_pgn_games(pgn_path)
    if not games:
        raise ValueError("No chess games were found in the PGN file")
    inputs, labels, tokenizer, sequence_length = build_training_examples(games)
    model = create_model(tokenizer.vocabulary_size, sequence_length)
    model.fit(inputs, labels, epochs=epochs, batch_size=batch_size, verbose=1)
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    Path(tokenizer_path).parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)
    tokenizer.save(tokenizer_path)
    return {
        "games": len(games),
        "examples": int(len(labels)),
        "sequence_length": sequence_length,
        "vocabulary_size": tokenizer.vocabulary_size,
    }


def main():
    parser = argparse.ArgumentParser(description="Train the chess SAN LSTM.")
    parser.add_argument("pgn_path", type=Path)
    parser.add_argument("--model", default="artifacts/chess_lstm.keras")
    parser.add_argument("--tokenizer", default="artifacts/chess_tokenizer.json")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    print(train(args.pgn_path, args.model, args.tokenizer, args.epochs, args.batch_size))


if __name__ == "__main__":
    main()
