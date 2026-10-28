import argparse
import random
from pathlib import Path

import numpy as np

from .fics_pipeline import (
    ChessSequence,
    prepare_fics_splits,
    save_metadata,
)
from .model import create_model, load_model, require_tensorflow


def train_fics(
    pgn_path,
    model_path="chess_lstm/chess_model_fics.keras",
    tokenizer_path="dataset/processed/fics_tokenizer.json",
    metadata_path="dataset/processed/fics_training_metadata.json",
    checkpoint_path="artifacts/fics_best.keras",
    window_size=128,
    batch_size=128,
    epochs=20,
    seed=42,
    resume=False,
):
    tf = require_tensorflow()
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)

    splits, tokenizer, metadata = prepare_fics_splits(
        pgn_path,
        seed=seed,
        window_size=window_size,
    )
    train_sequence = ChessSequence(
        splits.train, tokenizer, window_size, batch_size, shuffle=True, seed=seed
    )
    validation_sequence = ChessSequence(
        splits.validation, tokenizer, window_size, batch_size, shuffle=False, seed=seed
    )
    if not len(validation_sequence):
        raise ValueError("Validation split has no training examples")

    if resume and Path(checkpoint_path).exists():
        model = load_model(checkpoint_path)
    else:
        model = create_model(tokenizer.vocabulary_size, window_size, mask_zero=False)

    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            checkpoint_path, monitor="val_loss", save_best_only=True
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=3, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=1, min_lr=1e-6
        ),
    ]
    history = model.fit(
        train_sequence,
        validation_data=validation_sequence,
        epochs=epochs,
        callbacks=callbacks,
        verbose=1,
    )

    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)
    Path(tokenizer_path).parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(tokenizer_path)
    metadata.update(
        {
            "model_path": str(model_path),
            "tokenizer_path": str(tokenizer_path),
            "checkpoint_path": str(checkpoint_path),
            "epochs_requested": epochs,
            "epochs_completed": len(history.history["loss"]),
            "final_loss": float(history.history["loss"][-1]),
            "final_validation_loss": float(history.history["val_loss"][-1]),
        }
    )
    save_metadata(metadata, metadata_path)
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Train the separate FICS chess LSTM.")
    parser.add_argument("pgn_path", type=Path)
    parser.add_argument("--model", default="chess_lstm/chess_model_fics.keras")
    parser.add_argument("--tokenizer", default="dataset/processed/fics_tokenizer.json")
    parser.add_argument("--metadata", default="dataset/processed/fics_training_metadata.json")
    parser.add_argument("--checkpoint", default="artifacts/fics_best.keras")
    parser.add_argument("--window-size", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    print(train_fics(
        args.pgn_path, args.model, args.tokenizer, args.metadata,
        args.checkpoint, args.window_size, args.batch_size, args.epochs,
        args.seed, args.resume
    ))


if __name__ == "__main__":
    main()
