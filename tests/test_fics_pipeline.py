import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chess_lstm.fics_pipeline import (
    ChessSequence,
    count_examples,
    prepare_fics_splits,
    split_games,
)
from chess_lstm.tokenizer import ChessTokenizer


def test_game_split_is_reproducible_and_disjoint():
    games = [
        ["e4", "e5", "Nf3"],
        ["d4", "d5", "c4"],
        ["Nf3", "d5", "g3"],
        ["c4", "e5", "Nc3"],
        ["f4", "e5", "exf5"],
        ["b3", "e5", "Bb2"],
        ["g3", "d5", "Bg2"],
        ["a3", "d5", "b3"],
        ["h3", "d5", "a3"],
        ["Nc3", "Nf6", "e4"],
    ]
    first = split_games(games, seed=7)
    second = split_games(games, seed=7)
    assert first == second
    assert not set(map(tuple, first.train)) & set(map(tuple, first.validation))
    assert not set(map(tuple, first.train)) & set(map(tuple, first.test))


def test_sequence_windows_and_labels_are_bounded():
    games = [["e4", "e5", "Nf3", "Nc6", "Bb5"]]
    tokenizer = ChessTokenizer().fit(games)
    sequence = ChessSequence(games, tokenizer, window_size=2, batch_size=2)
    inputs, labels = sequence[0]
    assert inputs.shape == (2, 2)
    assert labels.shape == (2,)
    assert inputs.dtype == np.int32
    assert labels.dtype == np.int32
    assert sequence.example_count == count_examples(games)
    assert np.all(inputs >= 0)


def test_fics_preparation_reports_game_level_metadata(tmp_path):
    pgn = tmp_path / "games.pgn"
    pgn.write_text(
        '[Event "One"]\n\n1. e4 e5 2. Nf3 Nc6 1-0\n\n'
        '[Event "Two"]\n\n1. d4 d5 2. c4 e6 1/2-1/2\n',
        encoding="utf-8",
    )
    splits, tokenizer, metadata = prepare_fics_splits(
        pgn, validation_fraction=0.25, test_fraction=0.25, seed=3, window_size=2
    )
    assert metadata["total_games"] == 2
    assert metadata["train_games"] == 2
    assert metadata["window_size"] == 2
    assert tokenizer.vocabulary_size >= 2
    assert len(splits.validation) == 0
    assert len(splits.test) == 0
