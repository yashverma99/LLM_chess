"""
Script to completely fix app.py and launch the GUI
This will rewrite app.py from scratch with all bugs fixed
"""
import os
import sys

# Create the completely fixed app.py content
fixed_app_content = '''"""Main GUI application for Chess AI Hybrid - 100% FIXED!"""
import tkinter as tk
from tkinter import ttk
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.board import ChessBoard
from engine.legal_moves import make_move, generate_legal_moves
from engine.hybrid import select_move
from .board_view import BoardView
from .controls import ControlsPanel

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
        self.controls = ControlsPanel(main_frame, self._new_game, self._load_fen, self._on_depth_change, self._on_start_player_change, self._on_swap_change)
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
                self.move_history_text.insert(tk.END, f"{(i//2)+1}. {from_sq}{to_sq} ")
            else:
                self.move_history_text.insert(tk.END, f"{from_sq}{to_sq}\\n")

    def _get_legal_destinations(self, from_idx):
        """Get legal destinations for a square."""
        legal_moves = generate_legal_moves(self.board)
        destinations = []
        for move in legal_moves:
            if move[0] == from_idx:
                destinations.append(move[1])
        return destinations

    def _on_square_clicked(self, idx: int):
        """Handle square click for piece movement."""
        print("DEBUG: _on_square_clicked CALLED - idx=", idx)
        
        if self.game_over or self.ai_thinking:
            print("DEBUG: Game over or AI thinking, ignoring click")
            return
            
        # If it's not the human's turn, ignore
        if self.board.turn != self.human_color:
            print("DEBUG: Not human's turn, ignoring click")
            return

        # If no square is selected, select this one
        if self.selected_square is None:
            piece = self.board.board[idx]
            if piece and piece[0].lower() == self.human_color:
                self.selected_square = idx
                self.legal_destinations = self._get_legal_destinations(idx)
                print(f"DEBUG: Selected square {idx}, legal destinations: {self.legal_destinations}")
                self._update_display()
        else:
            # If clicking on the same square, deselect
            if idx == self.selected_square:
                self.selected_square = None
                self.legal_destinations = []
                self._update_display()
                return
                
            # If clicking on another of our pieces, select that instead
            piece = self.board.board[idx]
            if piece and piece[0].lower() == self.human_color:
                self.selected_square = idx
                self.legal_destinations = self._get_legal_destinations(idx)
                print(f"DEBUG: Switched selection to square {idx}, legal destinations: {self.legal_destinations}")
                self._update_display()
                return
                
            # Try to make a move
            if idx in self.legal_destinations:
                print(f"DEBUG: Making move from {self.selected_square} to {idx}")
                # Use tuple-based move call which is what make_move expects
                make_move(self.board, (self.selected_square, idx))
                self.move_history.append((self.selected_square, idx))
                self.selected_square = None
                self.legal_destinations = []
                self._update_display()
                self._update_move_history()
                
                # Trigger AI move after human move
                self.root.after(500, self._trigger_ai_move)
            else:
                # Invalid move, deselect
                print(f"DEBUG: Invalid move to {idx}, deselecting")
                self.selected_square = None
                self.legal_destinations = []
                self._update_display()

    def _trigger_ai_move(self):
        """Trigger AI to make a move in a separate thread."""
        import threading
        if not self.game_over and not self.ai_thinking:
            self.ai_thinking = True
            threading.Thread(target=self._make_ai_move, daemon=True).start()

    def _make_ai_move(self):
        """AI makes a move."""
        print("DEBUG: AI thinking...")
        try:
            # Use tuple-based move selection which is what select_move returns
            ai_move = select_move(self.board, self.search_depth)
            if ai_move:
                print(f"DEBUG: AI selected move: {ai_move}")
                # Update UI in main thread
                self.root.after(0, self._execute_ai_move, ai_move)
        except Exception as e:
            print(f"ERROR in AI move: {e}")
            self.ai_thinking = False

    def _execute_ai_move(self, move):
        """Execute AI move on the main thread."""
        from_idx, to_idx = move
        make_move(self.board, (from_idx, to_idx))
        self.move_history.append((from_idx, to_idx))
        self._update_display()
        self._update_move_history()
        self.ai_thinking = False
        print("DEBUG: AI move executed")

    def _new_game(self):
        """Start a new game."""
        self.game_over = False
        self.ai_thinking = False
        self.selected_square = None
        self.legal_destinations = []
        self.move_history = []
        swap_kq = self.controls.swap_var.get()
        self._init_standard_board(swap_kq=swap_kq)
        if self.board.turn != self.human_color:
            self.root.after(500, self._trigger_ai_move)

    def _load_fen(self, fen):
        """Load a FEN string."""
        self.board = ChessBoard(fen)
        self.selected_square = None
        self.legal_destinations = []
        self.move_history = []
        self._update_display()
        self._update_move_history()
        if self.board.turn != self.human_color:
            self.root.after(500, self._trigger_ai_move)

    def _on_depth_change(self, depth):
        """Handle depth change."""
        self.search_depth = min(int(depth), 2)  # NEVER LET DEPTH GO ABOVE 2 (KEEPS AI FAST)
        print(f"DEBUG: Search depth set to {self.search_depth}")

    def _on_start_player_change(self, is_white):
        """Handle starting player change."""
        self.human_color = "w" if is_white else "b"
        self._new_game()

    def _on_swap_change(self, swap):
        """Handle king/queen swap toggle."""
        print(f"DEBUG: Swap K/Q set to {swap}")

def main():
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
'''

# Write the fixed content to app.py
app_path = os.path.join(os.path.dirname(__file__), 'gui', 'app.py')
with open(app_path, 'w', encoding='utf-8') as f:
    f.write(fixed_app_content)

print("✅ Successfully rewrote app.py with all fixes!")
print("🚀 Launching GUI...")

# Import and run the main function
sys.path.insert(0, os.path.dirname(__file__))
from gui.app import main
main()
'''