# Hybrid Chess AI

This repository contains a custom chess engine and an independent,
chess-specific TensorFlow/Keras LSTM. The LSTM predicts SAN candidates, but it
never replaces legal move generation or minimax search.

## Components

- `engine/`: board, FEN, SAN, legal moves, evaluation, and alpha-beta search.
- `chess_lstm/`: chess tokenizer, PGN validation, inference, sample model, and
  the memory-bounded FICS training pipeline.
- `dataset/raw/`: sample and FICS PGN files.
- `dataset/processed/`: preprocessing artifacts and tokenizers.
- `tests/`: engine, PGN, LSTM, inference, and hybrid tests.

## Install

```powershell
python -m pip install -r requirements-chess-lstm.txt
python -m pip install python-chess
```

The custom engine itself does not import TensorFlow. `python-chess` is used for
PGN validation and dataset preparation.

## Test

```powershell
python -m pytest -q
```

## Train the separate FICS model

The checked-in `chess_lstm/chess_model.keras` is the original tiny sample
model. It is not overwritten. The FICS training command writes
`chess_lstm/chess_model_fics.keras` and
`dataset/processed/fics_tokenizer.json`.

```powershell
python -m chess_lstm.train_fics dataset\raw\fics_10000.pgn `
  --window-size 128 --batch-size 128 --epochs 20 --seed 42
```

This is a substantial CPU/memory workload. Training metrics must come from an
actual run; the repository does not claim that the FICS model is trained until
the command completes.

To resume from the best checkpoint:

```powershell
python -m chess_lstm.train_fics dataset\raw\fics_10000.pgn --resume
```

## Hybrid move selection

```python
from engine.hybrid import select_move

move, score, stats = select_move(board, history=["e4", "e5"], depth=3)
```

The hybrid layer orders the complete legal root move list using LSTM
candidates, then searches every legal root with alpha-beta. If model loading
or inference fails, it uses the original engine search.

## Benchmark

```powershell
python scripts\benchmark_search.py --depth 2
```

The benchmark reports elapsed time, nodes, cutoffs, and nodes per second. It
does not claim that hybrid ordering is stronger or faster without measured
comparisons.

## Limitations

The current custom move representation supports automatic queen promotion but
not underpromotion. Position-history draw rules such as threefold repetition
are not represented by `ChessBoard`. The LSTM is a next-SAN predictor trained
on game records, not a complete chess evaluation model.
