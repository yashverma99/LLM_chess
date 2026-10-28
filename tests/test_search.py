
from engine.board import ChessBoard
from engine.fen import load_fen, to_fen
from engine.search import find_best_move, minimax, INF
from engine.legal_moves import generate_legal_moves

board = ChessBoard()

# Test 1: Starting position
load_fen(
    board,
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
)

original_fen = to_fen(board)

move, score = find_best_move(board, depth=2)

assert move is not None
assert move in generate_legal_moves(board)
assert isinstance(score, int)

# Search must not modify the original board
assert to_fen(board) == original_fen

# Test 2: Black to move
load_fen(
    board,
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
)

move, score = find_best_move(board, depth=2)

assert move is not None
assert move in generate_legal_moves(board)

# Test 3: Checkmate position
load_fen(
    board,
    "7k/6Q1/5K2/8/8/8/8/8 b - - 0 1"
)

move, score = find_best_move(board, depth=2)

assert move is None
assert score is None

# Test 4: Invalid depth
try:
    find_best_move(board, depth=0)
    assert False
except ValueError:
    pass

print("ALL SEARCH TESTS PASSED!")
