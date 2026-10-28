# FICS Training Guide

## Dataset checks

The included FICS file has been checked with `python-chess`. It contains 10,000
legal parsed games, 9,938 unique move sequences, and 62 duplicate sequences.
Games are split before examples are created, preventing move-level leakage.

## Recommended configuration

The old artifact pads every example to 404 plies and requires roughly 1.2 GB
for the input array alone. The FICS pipeline defaults to a 128-ply sliding
window, which covers long context while bounding memory.

```powershell
python -m chess_lstm.train_fics dataset\raw\fics_10000.pgn `
  --window-size 128 --batch-size 128 --epochs 20 --seed 42
```

Outputs:

- `chess_lstm/chess_model_fics.keras`
- `dataset/processed/fics_tokenizer.json`
- `dataset/processed/fics_training_metadata.json`
- `artifacts/fics_best.keras`

Callbacks save the best validation-loss checkpoint, stop after validation
loss stalls, and reduce the learning rate on a plateau. `--resume` loads the
best checkpoint if it exists.

## Evaluation

The training history records loss and accuracy. Perplexity can be computed
from cross-entropy as `exp(validation_loss)` after a real training run. No
The approved run on the included FICS data completed six epochs before being
stopped because the CPU runtime for the remaining requested epochs was
impractical. It produced:

- training loss: `4.2990`;
- validation loss: `4.4400`;
- validation accuracy: `0.1531`;
- approximate validation perplexity: `84.7` (`exp(4.44)`).

These metrics describe next-token prediction on this dataset only. They do not
measure legal move quality or playing strength.

## Model limitations

The LSTM predicts SAN token likelihoods. It does not know legality by itself;
inference always validates SAN through the custom engine. The hybrid search
still evaluates every legal root move.
