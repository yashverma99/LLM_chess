
from engine.board import ChessBoard
from engine.fen import load_fen
from engine.moves import generate_all_moves, generate_piece_moves

board = ChessBoard()

# Starting position
load_fen(
    board,
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
)

moves = generate_all_moves(board)

# Starting position has 20 pseudo-legal moves
assert len(moves) == 20, len(moves)

# White pawn e2 has two moves
e2 = board.square_to_index("e2")
pawn_moves = generate_piece_moves(board, e2)

assert len(pawn_moves) == 2

# Knight b1 has two moves
b1 = board.square_to_index("b1")
knight_moves = generate_piece_moves(board, b1)

assert len(knight_moves) == 2

# Empty square has no moves
assert generate_piece_moves(board, board.square_to_index("e4")) == []

print("ALL MOVE GENERATION TESTS PASSED!")
