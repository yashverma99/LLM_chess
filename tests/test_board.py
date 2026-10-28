from engine.board import ChessBoard

board = ChessBoard()

assert len(board.board) == 64

assert board.square_to_index("a8") == 0
assert board.square_to_index("h8") == 7
assert board.square_to_index("a1") == 56
assert board.square_to_index("h1") == 63
assert board.square_to_index("e4") == 36

assert board.index_to_square(0) == "a8"
assert board.index_to_square(63) == "h1"
assert board.index_to_square(36) == "e4"

assert board.piece_at("e1") == "K" and board.piece_at("e8") == "k"

print("ALL BOARD TESTS PASSED!")
