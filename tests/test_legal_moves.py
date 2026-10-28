
from engine.board import ChessBoard
from engine.fen import load_fen
from engine.legal_moves import (
    generate_legal_moves,
    is_in_check,
    make_move,
    undo_move
)

board = ChessBoard()

# Test 1: Starting position
load_fen(
    board,
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
)

moves = generate_legal_moves(board)

assert len(moves) == 20, len(moves)

# Test 2: Check detection
load_fen(
    board,
    "4k3/8/8/8/8/8/4r3/4K3 w - - 0 1"
)

assert is_in_check(board, "w")

# Test 3: Make and undo move
load_fen(
    board,
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
)

original_fen = (
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
)

move = (
    board.square_to_index("e2"),
    board.square_to_index("e4")
)

state = make_move(board, move)
undo_move(board, move, state)

from engine.fen import to_fen

assert to_fen(board) == original_fen

# Test 4: Castling
load_fen(
    board,
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
)

moves = generate_legal_moves(board)

assert (
    board.square_to_index("e1"),
    board.square_to_index("g1")
) in moves

assert (
    board.square_to_index("e1"),
    board.square_to_index("c1")
) in moves

print("ALL LEGAL MOVE TESTS PASSED!")
