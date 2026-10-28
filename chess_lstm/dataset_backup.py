import re
from pathlib import Path

import numpy as np

from .tokenizer import ChessTokenizer


RESULT_TOKENS = {"1-0", "0-1", "1/2-1/2", "*"}


def _remove_variations(text):
    result = []
    depth = 0
    for character in text:
        if character == "(":
            depth += 1
        elif character == ")" and depth:
            depth -= 1
        elif depth == 0:
            result.append(character)
    return "".join(result)


def extract_san_moves(pgn):
    """Extract main-line SAN tokens from one PGN document."""
    moves_section = pgn.split("\n\n", 1)[1] if "\n\n" in pgn else pgn
    moves_section = re.sub(r"\{[^}]*\}", " ", moves_section, flags=re.DOTALL)
    moves_section = re.sub(r";[^\n]*", " ", moves_section)
    moves_section = _remove_variations(moves_section)
    tokens = moves_section.split()
    moves = []
    for token in tokens:
        token = re.sub(r"^\d+\.(?:\.\.)?", "", token)
        if token and token not in RESULT_TOKENS:
            moves.append(token)
    return moves


def load_pgn_games(path):
    """Return SAN move lists from all games in a PGN file."""
    content = Path(path).read_text(encoding="utf-8").strip()
    if not content:
        return []
    games = re.split(r"\n(?=\[Event\s)", content)
    return [extract_san_moves(game) for game in games if extract_san_moves(game)]


def build_training_examples(games, tokenizer=None):
    """Build padded prefixes and next-token labels from SAN games."""
    tokenizer = tokenizer or ChessTokenizer().fit(games)
    encoded_games = [tokenizer.encode(game) for game in games]
    max_length = max((len(game) - 1 for game in encoded_games), default=0)
    if max_length == 0:
        raise ValueError("At least one game with two moves is required")

    prefixes = []
    labels = []
    for game in encoded_games:
        for index in range(1, len(game)):
            prefix = game[:index]
            prefixes.append([0] * (max_length - len(prefix)) + prefix)
            labels.append(game[index])
    return np.asarray(prefixes, dtype=np.int32), np.asarray(labels, dtype=np.int32), tokenizer, max_length
