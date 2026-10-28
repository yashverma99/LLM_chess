
from engine.board import ChessBoard
from engine.fen import load_fen
from engine.evaluation import (
    evaluate_material,
    evaluate_position,
    evaluate_pawn_structure,
    evaluate_center_control,
    evaluate_king_safety
)

board = ChessBoard()

# Test 1: Starting position
load_fen(
    board,
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
)

assert evaluate_material(board) == 0

score = evaluate_position(board)

assert isinstance(score, int)

# Test 2: White has an extra queen
load_fen(
    board,
    "4k3/8/8/8/8/8/8/3QK3 w - - 0 1"
)

assert evaluate_material(board) == 900

# Test 3: Black has an extra queen
load_fen(
    board,
    "3qk3/8/8/8/8/8/8/4K3 w - - 0 1"
)

assert evaluate_material(board) == -900

# Test 4: Evaluation functions return integers
assert isinstance(evaluate_pawn_structure(board), int)
assert isinstance(evaluate_center_control(board), int)
assert isinstance(evaluate_king_safety(board), int)

print("ALL EVALUATION TESTS PASSED!")
print("Current position score:", evaluate_position(board))
