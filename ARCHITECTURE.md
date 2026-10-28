# Architecture

## Move selection

```text
ChessBoard
  -> generate_legal_moves()
  -> LSTM SAN probabilities (optional)
  -> SAN conversion and legal-move filtering
  -> root move ordering
  -> minimax + alpha-beta over every legal root
  -> selected move, score, and statistics
```

`engine/hybrid.py` treats LSTM output as ordering information only. A missing
model, invalid prediction, or empty legal candidate set falls back to the
original `engine.search.find_best_move`.

## Training

```text
PGN
  -> python-chess legal validation
  -> duplicate removal by canonical SAN sequence
  -> deterministic game-level train/validation/test split
  -> tokenizer fitted on training games only
  -> bounded sliding-window batches
  -> LSTM + dense vocabulary classifier
  -> best checkpoint, final model, tokenizer, metadata
```

FICS examples are generated on demand by `ChessSequence`; the full padded
example tensor is not materialized in memory.

## State safety

Search applies every temporary move through `make_move()` and restores it with
`undo_move()` in `finally` blocks. Existing two-value move tuples remain
unchanged.
