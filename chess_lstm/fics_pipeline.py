import json
import random
from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .dataset import load_pgn_games
from .tokenizer import ChessTokenizer

try:
    from tensorflow.keras.utils import Sequence as _KerasSequence
except ImportError:
    class _KerasSequence:
        pass


@dataclass(frozen=True)
class FicsSplits:
    train: list
    validation: list
    test: list


def split_games(games, validation_fraction=0.1, test_fraction=0.1, seed=42):
    if not 0 <= validation_fraction < 1 or not 0 <= test_fraction < 1:
        raise ValueError("Split fractions must be between 0 and 1")
    if validation_fraction + test_fraction >= 1:
        raise ValueError("Validation and test fractions leave no training games")

    shuffled = list(games)
    random.Random(seed).shuffle(shuffled)
    test_count = int(len(shuffled) * test_fraction)
    validation_count = int(len(shuffled) * validation_fraction)
    test = shuffled[:test_count]
    validation = shuffled[test_count:test_count + validation_count]
    train = shuffled[test_count + validation_count:]
    if not train:
        raise ValueError("The training split is empty")
    return FicsSplits(train=train, validation=validation, test=test)


def iter_encoded_examples(games, tokenizer, window_size):
    if window_size < 1:
        raise ValueError("Window size must be at least 1")
    for game in games:
        encoded = tokenizer.encode(game)
        for index in range(1, len(encoded)):
            prefix = encoded[max(0, index - window_size):index]
            yield (
                np.asarray(
                    [0] * (window_size - len(prefix)) + prefix,
                    dtype=np.int32,
                ),
                np.int32(encoded[index]),
            )


def count_examples(games):
    return sum(max(len(game) - 1, 0) for game in games)


class ChessSequence(_KerasSequence):
    """Memory-bounded Keras sequence that materializes only one batch."""

    def __init__(self, games, tokenizer, window_size, batch_size=128, shuffle=False, seed=42):
        self.encoded_games = [tokenizer.encode(game) for game in games]
        self.window_size = window_size
        self.batch_size = batch_size
        self.shuffle = shuffle
        self._random = random.Random(seed)
        self._offsets = []
        total = 0
        for game in self.encoded_games:
            total += max(len(game) - 1, 0)
            self._offsets.append(total)
        self.example_count = total
        self._indices = list(range(self.example_count))
        self.on_epoch_end()

    def __len__(self):
        return (self.example_count + self.batch_size - 1) // self.batch_size

    def _locate(self, flat_index):
        game_index = bisect_right(self._offsets, flat_index)
        previous_offset = self._offsets[game_index - 1] if game_index else 0
        move_index = flat_index - previous_offset + 1
        return self.encoded_games[game_index], move_index

    def __getitem__(self, batch_index):
        batch_indices = self._indices[
            batch_index * self.batch_size:(batch_index + 1) * self.batch_size
        ]
        inputs = []
        labels = []
        for flat_index in batch_indices:
            game, move_index = self._locate(flat_index)
            prefix = game[max(0, move_index - self.window_size):move_index]
            inputs.append([0] * (self.window_size - len(prefix)) + prefix)
            labels.append(game[move_index])
        return np.asarray(inputs, dtype=np.int32), np.asarray(labels, dtype=np.int32)

    def on_epoch_end(self):
        if self.shuffle:
            self._random.shuffle(self._indices)


def prepare_fics_splits(
    pgn_path,
    validation_fraction=0.1,
    test_fraction=0.1,
    seed=42,
    window_size=128,
):
    games = load_pgn_games(pgn_path)
    splits = split_games(games, validation_fraction, test_fraction, seed)
    tokenizer = ChessTokenizer().fit(splits.train)
    return splits, tokenizer, {
        "source": str(Path(pgn_path)),
        "seed": seed,
        "window_size": window_size,
        "total_games": len(games),
        "train_games": len(splits.train),
        "validation_games": len(splits.validation),
        "test_games": len(splits.test),
        "train_examples": count_examples(splits.train),
        "validation_examples": count_examples(splits.validation),
        "test_examples": count_examples(splits.test),
        "vocabulary_size": tokenizer.vocabulary_size,
    }


def save_metadata(metadata, path):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
