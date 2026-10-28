import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chess_lstm.dataset import build_training_examples, load_pgn_games


def main():
    parser = argparse.ArgumentParser(description="Preprocess PGN games for the chess LSTM.")
    parser.add_argument("pgn_path", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/chess_dataset.npz"))
    parser.add_argument("--tokenizer", type=Path, default=Path("artifacts/chess_tokenizer.json"))
    args = parser.parse_args()

    games = load_pgn_games(args.pgn_path)
    inputs, labels, tokenizer, sequence_length = build_training_examples(games)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output = args.output.with_suffix(".npz")
    np.savez_compressed(
        args.output,
        inputs=inputs,
        labels=labels,
        sequence_length=sequence_length,
    )
    args.tokenizer.parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(args.tokenizer)
    print(f"Games: {len(games)}")
    print(f"Examples: {len(labels)}")
    print(f"Sequence length: {sequence_length}")
    print(f"Dataset: {args.output}")
    print(f"Tokenizer: {args.tokenizer}")


if __name__ == "__main__":
    main()
