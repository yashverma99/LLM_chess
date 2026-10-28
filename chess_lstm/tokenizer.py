import json
from pathlib import Path


class ChessTokenizer:
    """Maps SAN move tokens to stable integer IDs for the chess model."""

    PAD_TOKEN = "<PAD>"
    UNKNOWN_TOKEN = "<UNK>"

    def __init__(self):
        self.token_to_id = {
            self.PAD_TOKEN: 0,
            self.UNKNOWN_TOKEN: 1,
        }
        self.id_to_token = {
            0: self.PAD_TOKEN,
            1: self.UNKNOWN_TOKEN,
        }

    @property
    def vocabulary_size(self):
        return len(self.token_to_id)

    def fit(self, games):
        tokens = sorted({token for game in games for token in game})
        for token in tokens:
            if token not in self.token_to_id:
                token_id = len(self.token_to_id)
                self.token_to_id[token] = token_id
                self.id_to_token[token_id] = token
        return self

    def encode(self, moves):
        return [
            self.token_to_id.get(move, self.token_to_id[self.UNKNOWN_TOKEN])
            for move in moves
        ]

    def decode(self, ids):
        return [self.id_to_token.get(int(token_id), self.UNKNOWN_TOKEN) for token_id in ids]

    def save(self, path):
        output_path = Path(path)
        output_path.write_text(
            json.dumps({"token_to_id": self.token_to_id}, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        tokenizer = cls()
        tokenizer.token_to_id = {
            str(token): int(token_id)
            for token, token_id in data["token_to_id"].items()
        }
        tokenizer.id_to_token = {
            token_id: token for token, token_id in tokenizer.token_to_id.items()
        }
        return tokenizer
