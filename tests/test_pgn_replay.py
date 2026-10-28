import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.board import ChessBoard
from engine.fen import load_fen, to_fen
from engine.legal_moves import make_move
from engine.san import san_to_move


STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
RESULTS = {"1-0", "0-1", "1/2-1/2", "*"}


def extract_san_moves(pgn):
    moves_section = pgn.split("\n\n", 1)[1]
    tokens = moves_section.split()
    return [
        token
        for token in tokens
        if not re.fullmatch(r"\d+\.+", token) and token not in RESULTS
    ]


pgn_path = Path(__file__).resolve().parents[1] / "dataset" / "raw" / "sample.pgn"
san_moves = extract_san_moves(pgn_path.read_text(encoding="utf-8"))

assert len(san_moves) == 10, f"Expected 10 SAN moves, found {len(san_moves)}"

board = ChessBoard()
load_fen(board, STARTING_FEN)

for ply, san in enumerate(san_moves, start=1):
    move_number = (ply + 1) // 2
    try:
        move = san_to_move(board, san)
        make_move(board, move)
    except (ValueError, IndexError, TypeError) as error:
        raise AssertionError(
            f"Move {move_number} ({san!r}) failed: {error}"
        ) from error

print("Final board:")
board.display()
print("Final FEN:")
print(to_fen(board))
print(f"Successfully replayed {len(san_moves)} SAN moves.")
