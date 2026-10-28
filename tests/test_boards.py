
from engine.board import ChessBoard

board = ChessBoard()

# Test 1: Total squares
assert len(board.board) == 64

# Test 2: Square to index
assert board.square_to_index("a8") == 0
assert board.square_to_index("h8") == 7
assert board.square_to_index("a1") == 56
assert board.square_to_index("h1") == 63
assert board.square_to_index("e4") == 36

# Test 3: Index to square
assert board.index_to_square(0) == "a8"
assert board.index_to_square(63) == "h1"
assert board.index_to_square(36) == "e4"

# Test 4: Initial board is empty
assert board.piece_at("e1") == "K" and board.piece_at("e8") == "k"

print("ALL BOARD TESTS PASSED!")
