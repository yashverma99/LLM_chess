"""Integration tests for the Chess GUI."""
import pytest
from engine.board import ChessBoard
from engine.fen import load_fen, to_fen
from engine.legal_moves import generate_legal_moves, make_move
from engine.hybrid import select_move


def test_board_initialization():
    """Test that the board initializes correctly with standard position."""
    board = ChessBoard()
    # Setup standard position
    board.board = [
        "r", "n", "b", "q", "k", "b", "n", "r",
        "p", "p", "p", "p", "p", "p", "p", "p",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        "P", "P", "P", "P", "P", "P", "P", "P",
        "R", "N", "B", "Q", "K", "B", "N", "R"
    ]
    board.turn = "w"
    
    # Verify initial state
    assert board.board[60] == "K"  # White king on e1
    assert board.board[4] == "k"    # Black king on e8
    assert board.turn == "w"


def test_fen_loading():
    """Test that FEN strings load correctly."""
    board = ChessBoard()
    test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    load_fen(board, test_fen)
    
    # Verify FEN is preserved
    generated_fen = to_fen(board)
    assert generated_fen == test_fen


def test_legal_moves_generation():
    """Test that legal moves are generated correctly for initial position."""
    board = ChessBoard()
    # Setup standard position
    board.board = [
        "r", "n", "b", "q", "k", "b", "n", "r",
        "p", "p", "p", "p", "p", "p", "p", "p",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        "P", "P", "P", "P", "P", "P", "P", "P",
        "R", "N", "B", "Q", "K", "B", "N", "R"
    ]
    board.turn = "w"
    
    legal_moves = generate_legal_moves(board)
    # Initial position has 20 legal moves
    assert len(legal_moves) == 20


def test_hybrid_move_selection():
    """Test that the hybrid engine can select a move."""
    board = ChessBoard()
    # Setup standard position
    board.board = [
        "r", "n", "b", "q", "k", "b", "n", "r",
        "p", "p", "p", "p", "p", "p", "p", "p",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        "P", "P", "P", "P", "P", "P", "P", "P",
        "R", "N", "B", "Q", "K", "B", "N", "R"
    ]
    board.turn = "w"
    
    # Call select_move with minimal depth (engine fallback mode will work even if LSTM isn't loaded)
    best_move, score, stats = select_move(board, depth=1)
    
    # Should return a valid move
    assert best_move is not None
    assert score is not None
    assert stats is not None
    assert isinstance(best_move, tuple)
    assert len(best_move) == 2


def test_make_move():
    """Test that making a move updates the board correctly."""
    board = ChessBoard()
    # Setup standard position
    board.board = [
        "r", "n", "b", "q", "k", "b", "n", "r",
        "p", "p", "p", "p", "p", "p", "p", "p",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        ".", ".", ".", ".", ".", ".", ".", ".",
        "P", "P", "P", "P", "P", "P", "P", "P",
        "R", "N", "B", "Q", "K", "B", "N", "R"
    ]
    board.turn = "w"
    
    # Make e2-e4 move (index 52 to 36)
    move = (52, 36)
    old_state = make_move(board, move)
    
    # Verify pawn moved
    assert board.board[36] == "P"
    assert board.board[52] == "."
    assert board.turn == "b"  # Turn switched to black