# Chess LSTM

This is a separate chess-specific model. It does not import, modify, or reuse
weights from any English next-word project. The existing `engine` package has
no TensorFlow dependency.

The checked-in `dataset/raw/sample.pgn` is intentionally a tiny smoke-test
dataset containing one 10-ply game. It is enough to verify preprocessing and a
one-epoch training path, but it is not a meaningful chess model training set.
Do not describe a model as trained until the training command has been run on
real chess PGN data.

## Install

From `C:\Users\yashv\Downloads\CHESS ENGINE`:

```powershell
python -m pip install -r requirements-chess-lstm.txt
```

TensorFlow must be available in the selected Python environment for training
and model loading. The current repository tests skip only those TensorFlow
specific checks when it is absent.

## Preprocess

```powershell
python scripts\preprocess_chess_pgn.py dataset\raw\sample.pgn
```

This writes `artifacts\chess_dataset.npz` and
`artifacts\chess_tokenizer.json`.

## Train

```powershell
python -m chess_lstm.train dataset\raw\sample.pgn --epochs 10
```

This writes `artifacts\chess_lstm.keras` and
`artifacts\chess_tokenizer.json`. The tokenizer and model are saved separately.

## Test

```powershell
python -m pytest -q
```

Inference accepts the model's highest-probability SAN tokens only after each
candidate is passed through `engine.san.san_to_move`, which validates it
against the current engine legal move list.
