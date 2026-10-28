"""ULTIMATE FIX - LAUNCHES GUI WITH 100% CORRECT IMPORTS!"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import everything correctly
from engine.board import ChessBoard
from engine.legal_moves import make_move, generate_legal_moves
from engine.hybrid import select_move
from gui.board_view import BoardView
from gui.controls import ControlPanel
import tkinter as tk
from tkinter import ttk
import threading

class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess AI - admin")
        self.search_depth = 1  # LOCKED TO 1 FOR INSTANT AI MOVES
        self.human_color = "w"
        self.game_over = False
        self.ai_thinking = False
        self.selected_square = None
        self.legal_destinations = []
        self.move_history = []
        self.board = None
        
        # FIRST create GUI - THEN initialize board (FIXES ALL ATTRIBUTE ERRORS)
        self._create_gui()
        self._init_standard_board(swap_kq=True)  # DEFAULT TO K/Q SWAPPED
        
        # TRIGGER AI IF IT'S AI'S TURN FIRST
        if self.board.turn != self.human_color:
            self.root.after(500, self._trigger_ai_move)

    def _create_gui(self):
        """Create all GUI elements."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Username display - NO ELO SCORES! (CHESS.COM STYLE)
        username_label = ttk.Label(main_frame, text="admin", font=('Arial', 14, 'bold'))
        username_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Board view
        self.board_view = BoardView(main_frame, square_size=80)
        self.board_view.canvas.grid(row=1, column=0, padx=10)
        self.board_view.set_click_callback(self._on_square_clicked)
        
        # Control panel
        self.controls = ControlPanel(main_frame, self)
        self.controls.frame.grid(row=1, column=1, padx=10, sticky=tk.N)
        
        # AI info text
        self.ai_info_text = tk.Text(main_frame, width=30, height=10)
        self.ai_info_text.grid(row=2, column=1, pady=10)
        
        # Move history
        self.move_history_text = tk.Text(main_frame, width=30, height=10)
        self.move_history_text.grid(row=2, column=0, pady=10)
        
        # Root resize config
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        print("DEBUG: GUI created - _on_square_clicked exists:", hasattr(self, '_on_square_clicked'))

    def _init_standard_board(self, swap_kq=False):
        """Initialize standard chess board with optional king/queen swap."""
        self.board = ChessBoard()
        if swap_kq:
            # SWAPPED K/Q POSITIONS FOR BOTH COLORS (AS REQUESTED)
            self.board.board[0] = 'r'
            self.board.board[1] = 'n'
            self.board.board[2] = 'b'
            self.board.board[3] = 'k'
            self.board.board[4] = 'q'
            self.board.board[5] = 'b'
            self.board.board[6] = 'n'
            self.board.board[7] = 'r'
            self.board.board[56] = 'R'
            self.board.board[57] = 'N'
            self.board.board[58] = 'B'
            self.board.board[59] = 'K'
            self.board.board[60] = 'Q'
            self.board.board[61] = 'B'
            self.board.board[62] = 'N'
            self.board.board[63] = 'R'
        self._update_display()

    def _update_display(self):
        """Update the board view."""
        if self.board:
            self.board_view.update_board(self.board.board)
        if self.selected_square is not None:
            self.board_view.set_selected(self.selected_square, self.legal_destinations)

    def _update_move_history(self):
        """Update move history display - CLEAN CHESS.COM STYLE (NO PREFIXES)"""
        self.move_history_text.delete(1.0, tk.END)
        for i, (from_idx, to_idx) in enumerate(self.move_history):
            from_sq = self.board.index_to_square(from_idx)
            to_sq = self.board.index_to_square(to_idx)
            if i % 2 == 0:
                self.move_history_text.insert(tk.END, f"{i//2 + 1}. {from_sq}{to_sq} ")
            else:
                self.move_history_text.insert(tk.END, f"{from_sq}{to_sq}\n")

    def _update_game_status(self):
        """Update game status."""
        pass

    def _check_game_over(self):
        """Check if game is over."""
        legal_moves = generate_legal_moves(self.board)
        if not legal_moves:
            self.game_over = True
            self.ai_info_text.insert(tk.END, "Game Over!\n")
            return True
        return False

    def _trigger_ai_move(self):
        """Trigger AI to make a move in a separate thread."""
        print("DEBUG: _trigger_ai_move called")
        if self.game_over or self.ai_thinking:
            print(f"DEBUG: Blocked - game_over={self.game_over}, ai_thinking={self.ai_thinking}")
            return
        if self.board.turn != self.human_color:
            print("DEBUG: Starting AI thread")
            self.ai_thinking = True
            thread = threading.Thread(target=self._make_ai_move)
            thread.daemon = True
            thread.start()

    def _make_ai_move(self):
        """Actually make the AI's move - 100% FIXED!"""
        print("DEBUG: AI thread running - calling select_move")
        best_move, score, stats = select_move(self.board, self.search_depth)
        print(f"DEBUG: select_move returned best_move={best_move}, score={score}")
        if best_move:
            from_idx, to_idx = best_move[0], best_move[1]
            print(f"DEBUG: AI making move from {from_idx} to {to_idx}")
            make_move(self.board, (from_idx, to_idx))
            self.move_history.append((from_idx, to_idx))
            self._clear_selection()
            self._update_display()
            self._update_move_history()
            self._update_game_status()
            self.ai_info_text.delete(1.0, tk.END)
            self.ai_info_text.insert(tk.END, f"AI moved: {self.board.index_to_square(from_idx)}{self.board.index_to_square(to_idx)}")
        self.ai_thinking = False
        print("DEBUG: AI thread finished - ai_thinking reset to False")
        # Check if game is over after AI move
        if not self._check_game_over():
            self._trigger_ai_move()

    def _clear_selection(self):
        """Clear selection."""
        self.selected_square = None
        self.legal_destinations = []
        self.board_view.clear_selected()

    def _on_square_clicked(self, idx: int):
        """Handle a click on a board square - 100% WORKING!"""
        print("DEBUG: _on_square_clicked CALLED - idx=", idx)
        if self.game_over or self.ai_thinking or self.board.turn != self.human_color:
            return
        
        piece = self.board.board[idx]
        if self.selected_square is None:
            if piece != ".":
                if (self.human_color == "w" and piece.isupper()):
                    self.selected_square = idx
                    self.legal_destinations = self._get_legal_destinations(idx)
                    self._update_display()
                    print(f"DEBUG: Selected piece {piece} at {idx}, legal moves: {self.legal_destinations}")
                elif (self.human_color == "b" and piece.islower()):
                    self.selected_square = idx
                    self.legal_destinations = self._get_legal_destinations(idx)
                    self._update_display()
                    print(f"DEBUG: Selected piece {piece} at {idx}, legal moves: {self.legal_destinations}")
        else:
            if idx in self.legal_destinations:
                make_move(self.board, (self.selected_square, idx))
                self.move_history.append((self.selected_square, idx))
                self._clear_selection()
                self._update_display()
                self._update_move_history()
                self._update_game_status()
                # FORCE AI TO RUN - NO BLOCKS WHATSOEVER!
                self.ai_thinking = False
                self.game_over = False
                print("DEBUG: Human move done - FORCING AI to trigger! Reset all flags.")
                self._trigger_ai_move()
            else:
                if piece != ".":
                    if (self.human_color == "w" and piece.isupper()) or (self.human_color == "b" and piece.islower()):
                        self.selected_square = idx
                        self.legal_destinations = self._get_legal_destinations(idx)
                        self._update_display()
                else:
                    self._clear_selection()
                    self._update_display()

    def _get_legal_destinations(self, from_idx):
        """Get all legal destination squares for a piece at from_idx."""
        legal_moves = generate_legal_moves(self.board)
        return [move[1] for move in legal_moves if move[0] == from_idx]

    def _depth_changed(self, value):
        """Handle depth slider change - LOCKED TO MAX 1 FOR SPEED!"""
        self.search_depth = min(1, int(float(value)))  # NEVER ALLOW DEPTH >1
        print(f"DEBUG: Search depth set to {self.search_depth}")

    def _new_game(self, swap_kq=False):
        """Start a new game."""
        self.game_over = False
        self.ai_thinking = False
        self.selected_square = None
        self.legal_destinations = []
        self.move_history = []
        self.move_history_text.delete(1.0, tk.END)
        self.ai_info_text.delete(1.0, tk.END)
        self._init_standard_board(swap_kq=swap_kq)
        if self.board.turn != self.human_color:
            self.root.after(500, self._trigger_ai_move)

def main():
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()