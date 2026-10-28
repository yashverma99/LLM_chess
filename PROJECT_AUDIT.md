# Chess AI Project Audit

## Scope and baseline

This audit covers the custom chess engine, SAN/PGN handling, chess-specific
LSTM pipeline, hybrid move ordering, tests, and the checked-in FICS artifacts.
It was performed against the repository as it exists on 2026-10-25.

Baseline command:

```powershell
python -m pytest -q
```

Result: **10 passed, 9 warnings**. The warnings are from Python 3.14 package
compatibility and Keras masking/deprecation behavior; they are not hidden.

## Current architecture

```text
PGN
  -> chess_lstm.dataset (python-chess validation, SAN extraction, deduplication)
  -> chess_lstm.tokenizer (SAN token IDs)
  -> chess_lstm.model (TensorFlow/Keras LSTM)
  -> chess_lstm.inference (probability ranking + SAN + engine legality filter)
  -> engine.hybrid (LSTM root ordering only)
  -> engine.search (all legal roots, minimax + alpha-beta)
```

The core `engine` package has no TensorFlow dependency. The LSTM is advisory:
the hybrid layer must continue searching every legal root move.

## Completed features

- Board representation, FEN load/save, pseudo-legal and legal move generation.
- Castling, en passant, check detection, SAN conversion, move undo.
- Minimax with alpha-beta pruning and a position evaluation function.
- PGN replay test and SAN legality tests.
- Chess-specific tokenizer with persistence.
- TensorFlow/Keras sample model and separate tokenizer.
- Full-vocabulary LSTM candidate ranking with legal filtering.
- Hybrid search that uses LSTM candidates for ordering and falls back to the
  original search when LSTM loading or inference fails.
- FICS PGN extraction and an initial processed artifact.

## Verified dataset facts

`dataset/raw/fics_10000.pgn` contains:

- 10,000 parsed games.
- 10,000 games with legal main lines and no parser errors.
- 62 duplicate move sequences.
- 9,938 unique move sequences after deduplication.
- 10 to 405 plies per game, averaging 75.5526 plies.

The current processed artifact contains 742,864 examples with a 404-token
fixed sequence length. An `int32` input array is approximately 1.2 GB before
TensorFlow overhead. This is not an appropriate default for a small desktop
training workflow.

## Critical findings

### High priority

1. **FICS training is not game-split.** The existing preprocessing produces one
   large array and has no train/validation/test partition, so validation leakage
   is possible if added naively.
2. **Fixed padding wastes memory.** Most prefixes are much shorter than 404
   tokens. Fixed windows should be generated per game with a configurable
   maximum length and streamed in batches.
3. **No training metadata or reproducibility contract.** Seed, source hash,
   split counts, vocabulary size, sequence length, and configuration are not
   saved beside a model.
4. **No callbacks or resume path.** The current training script calls `fit`
   once, saves only after completion, and cannot resume from a checkpoint.
5. **The checked-in `chess_lstm/chess_model.keras` is the tiny sample model.**
   It must remain untouched while a FICS model is trained separately.

### Medium priority

1. The current Keras model uses `mask_zero=True` with an LSTM path that emits a
   masking warning. The improved FICS model should use explicit fixed windows
   with a non-masking embedding or a verified mask-aware architecture.
2. Search returns only move and score; node counts, cutoffs, and elapsed time
   are not exposed.
3. The custom engine has no position-history object, so threefold repetition and
   automatic draw claims cannot be represented by the current board alone.
4. SAN promotion accepts only queen promotion. Underpromotion is not supported
   by the existing two-integer move representation.
5. FEN validation does not enforce all semantic constraints, such as exactly
   one king per side or legal castling-piece placement.

### Low priority

1. There is no user-facing CLI or GUI.
2. Documentation is limited to `CHESS_LSTM.md`; architecture, training,
   benchmark, and project-level documentation are missing.
3. The direct script tests need `sys.path` bootstrapping, while pytest works
   from the repository root.

## Recommended implementation plan

1. Add a separate FICS pipeline that:
   - validates standard games;
   - deduplicates by canonical main-line SAN;
   - splits by game before creating examples;
   - uses configurable sliding windows;
   - streams batches without materializing the 1.2 GB tensor;
   - saves tokenizer, metadata, and split manifests;
   - supports seeds, checkpoint resume, early stopping, and learning-rate
     reduction.
2. Add a separate `chess_model_fics.keras`; never overwrite the sample model.
3. Add data-quality and pipeline tests using small fixtures.
4. Add search statistics and benchmark scripts without changing move behavior.
5. Expand rule tests before considering engine-rule changes. Underpromotion and
   repetition require an explicit move/state API decision and should not be
   patched speculatively.
6. Add README, architecture, training, and benchmark documentation.
7. Request approval before running a substantial FICS training job; training
   metrics must come from an actual run and will not be fabricated.

## Completed since the initial audit

- Added a game-level, deterministic FICS split and training-only tokenizer fit.
- Added bounded sliding-window batches through a Keras-compatible sequence.
- Added metadata, checkpoints, early stopping, learning-rate reduction, and
  resume support.
- Trained and saved a separate six-epoch FICS model after approval.
- Added search node/cutoff statistics and a reproducible benchmark script.
- Added README, architecture, training, and benchmark documentation.

## Remaining work

- Decide and implement a backward-compatible draw/repetition state model.
- Add underpromotion without breaking the current two-integer move API.
- Add a lightweight CLI or GUI if an interactive interface is required.
- Run longer FICS training on a faster or accelerated environment if better
  predictive metrics are desired.
