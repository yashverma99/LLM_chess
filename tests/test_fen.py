
from engine.board import ChessBoard
from engine.fen import load_fen, to_fen

board = ChessBoard()

starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

load_fen(board, starting_fen)

assert len(board.board) == 64
assert board.board[0] == "r"
assert board.board[4] == "k"
assert board.board[60] == "K"
assert board.turn == "w"

generated_fen = to_fen(board)

assert generated_fen == starting_fen

print("ALL FEN TESTS PASSED!")
