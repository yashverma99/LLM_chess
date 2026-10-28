import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.board import ChessBoard
from engine.fen import load_fen
from engine.legal_moves import make_move
from engine.san import san_to_move


STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def play(board, notation):
    move = san_to_move(board, notation)
    make_move(board, move)
    return move


board = ChessBoard()
load_fen(board, STARTING_FEN)

assert play(board, "e4") == (
    board.square_to_index("e2"),
    board.square_to_index("e4"),
)
assert play(board, "e5") == (
    board.square_to_index("e7"),
    board.square_to_index("e5"),
)
assert play(board, "Nf3") == (
    board.square_to_index("g1"),
    board.square_to_index("f3"),
)
assert play(board, "Nc6") == (
    board.square_to_index("b8"),
    board.square_to_index("c6"),
)
assert play(board, "Bb5") == (
    board.square_to_index("f1"),
    board.square_to_index("b5"),
)
assert play(board, "a6") == (
    board.square_to_index("a7"),
    board.square_to_index("a6"),
)
assert play(board, "Bxc6") == (
    board.square_to_index("b5"),
    board.square_to_index("c6"),
)

load_fen(board, "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
assert play(board, "O-O") == (
    board.square_to_index("e1"),
    board.square_to_index("g1"),
)

load_fen(board, "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
assert play(board, "O-O-O") == (
    board.square_to_index("e1"),
    board.square_to_index("c1"),
)

load_fen(board, "4k3/8/8/8/8/8/3R4/3rK3 w - - 0 1")
assert play(board, "Rxd1") == (
    board.square_to_index("d2"),
    board.square_to_index("d1"),
)

load_fen(board, "4k3/8/5N2/8/8/8/8/1N2K3 w - - 0 1")
assert play(board, "Nbd2") == (
    board.square_to_index("b1"),
    board.square_to_index("d2"),
)

load_fen(board, "4k3/8/4R3/8/8/8/8/K3R3 w - - 0 1")
assert play(board, "R1e2") == (
    board.square_to_index("e1"),
    board.square_to_index("e2"),
)

load_fen(board, "4k3/8/8/8/8/8/8/K5Q1 w - - 0 1")
assert san_to_move(board, "Qg8+") == (
    board.square_to_index("g1"),
    board.square_to_index("g8"),
)

load_fen(board, "7k/5K2/8/8/8/8/8/6Q1 w - - 0 1")
try:
    san_to_move(board, "Qg7+")
except ValueError:
    pass
else:
    raise AssertionError("Incorrect checkmate suffix was accepted")

load_fen(board, "4k3/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
try:
    san_to_move(board, "R1e2")
except ValueError:
    pass
else:
    raise AssertionError("Ambiguous or illegal SAN was accepted")

print("ALL SAN TESTS PASSED!")
