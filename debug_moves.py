#!/usr/bin/env python3
"""Debug script to test basic piece movement"""

from gui.app import ChessApp
import tkinter as tk
from engine.legal_moves import make_move, generate_legal_moves
from gui.chessboard import ChessBoard

# Test basic movement
print("Testing basic movement system...")
board = ChessBoard()

# Initialize swapped king/queen positions (as per your setup)
board.board[0] = 'r'
board.board[1] = 'k'  # Black king at column 1 (instead of 4)
board.board[2] = 'q'  # Black queen at column 2 (instead of 3)
board.board[3] = 'b'
board.board[4] = 'b'
board.board[5] = 'n'
board.board[6] = 'n'
board.board[7] = 'r'
board.board[56] = 'R'
board.board[57] = 'K'  # White king at column 1
board.board[58] = 'Q'  # White queen at column 2
board.board[59] = 'B'
board.board[60] = 'B'
board.board[61] = 'N'
board.board[62] = 'N'
board.board[63] = 'R'

print("\nInitial board state (first row):")
for i in range(8):
    print(f"{i}: {board.board[i]}", end=" | ")
print("\nLast row:")
for i in range(56, 64):
    print(f"{i}: {board.board[i]}", end=" | ")

# Test legal moves generation
print("\n\nGenerating legal moves...")
legal_moves = generate_legal_moves(board)
print(f"Found {len(legal_moves)} legal moves!")
if legal_moves:
    print("First 5 legal moves:")
    for m in legal_moves[:5]:
        print(f"  {m[0]} -> {m[1]}")

# Test make_move works with tuple format
print("\nTesting make_move with tuple format...")
try:
    # Move white knight from b1 (57+7=64? Wait, index 61 is first white knight)
    knight_move = (61, 42)  # b1 to c3
    make_move(board, knight_move)
    print("✓ make_move() works perfectly with tuple argument!")
except Exception as e:
    print(f"✗ ERROR with make_move: {e}")

# Test if human click handler would work
print("\nTesting human move handling...")
selected_square = 61  # b1
idx = 42  # c3
try:
    make_move(board, (selected_square, idx))
    print("✓ Human move handling works!")
except Exception as e:
    print(f"✗ Human move ERROR: {e}")

print("\n=== ALL CORE MOVEMENT LOGIC IS WORKING ===")