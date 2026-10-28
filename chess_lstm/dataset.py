
import re
from pathlib import Path

import chess
import chess.pgn
import numpy as np

from .tokenizer import ChessTokenizer


RESULT_TOKENS = {"1-0", "0-1", "1/2-1/2", "*"}


def extract_san_moves(pgn):
    """Extract main-line SAN tokens from one PGN document."""
    game = chess.pgn.read_game(__import__("io").StringIO(pgn))

    if game is None or game.errors:
        return []

    board = game.board()
    moves = []

    try:
        for move in game.mainline_moves():
            if move not in board.legal_moves:
                return []
            moves.append(board.san(move))
            board.push(move)
    except (ValueError, AssertionError):
        return []

    return moves


def load_pgn_games(path):
    """Load, validate and deduplicate games from a PGN file."""
    games = []
    seen = set()

    with Path(path).open("r", encoding="utf-8-sig") as file:
        while True:
            game = chess.pgn.read_game(file)

            if game is None:
                break

            if game.errors:
                continue
            if game.headers.get("Variant", "Standard").lower() != "standard":
                continue

            board = game.board()
            moves = []

            try:
                for move in game.mainline_moves():
                    if move not in board.legal_moves:
                        moves = []
                        break

                    moves.append(board.san(move))
                    board.push(move)
            except (ValueError, AssertionError):
                continue

            if len(moves) < 2:
                continue

            key = tuple(moves)
            if key in seen:
                continue

            seen.add(key)
            games.append(moves)

    return games


def build_training_examples(games, tokenizer=None):
    """Build padded prefixes and next-token labels from SAN games."""
    if not games:
        raise ValueError("No valid chess games found")

    tokenizer = tokenizer or ChessTokenizer().fit(games)
    encoded_games = [tokenizer.encode(game) for game in games]

    max_length = max(
        (len(game) - 1 for game in encoded_games),
        default=0,
    )

    if max_length == 0:
        raise ValueError("At least one game with two moves is required")

    prefixes = []
    labels = []

    for game in encoded_games:
        for index in range(1, len(game)):
            prefix = game[:index]
            prefixes.append(
                [0] * (max_length - len(prefix)) + prefix
            )
            labels.append(game[index])

    return (
        np.asarray(prefixes, dtype=np.int32),
        np.asarray(labels, dtype=np.int32),
        tokenizer,
        max_length,
    )
