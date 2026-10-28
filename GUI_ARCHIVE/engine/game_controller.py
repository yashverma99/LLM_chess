"""Game controller that manages chess game state and coordinates between GUI and LLM."""
from PySide6.QtCore import QObject, Signal
from engine.board import ChessBoard
from engine.fen import load_fen, to_fen
from engine.legal_moves import generate_legal_moves, make_move, undo_move
from engine.san import move_to_san
from engine.llm_adapter import LLMAdapter
from typing import Optional, Tuple, List, Dict, Any

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class GameController(QObject):
    """Central controller for the chess game."""
    
    # Signals for game state changes
    board_updated = Signal()
    move_made = Signal(object, str)  # move, san
    game_over = Signal(str)  # reason
    ai_thinking = Signal(bool)
    ai_status_updated = Signal(str)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.board = ChessBoard()
        self.move_history: List[str] = []
        self.board_history: List[Tuple] = []  # For undo/redo
        self.redo_history: List[Tuple] = []
        
        # Game mode settings
        self.white_is_ai = False
        self.black_is_ai = False
        self.ai_depth = 3
        
        # LLM adapter
        self.llm_adapter = LLMAdapter()
        self.llm_adapter.move_ready.connect(self._on_ai_move_ready)
        self.llm_adapter.error.connect(self._on_ai_error)
        self.llm_adapter.status_changed.connect(self._on_ai_status_changed)
        
        self._is_ai_turn = False
        self._game_over = False

        # Start new game
        self.new_game()

    def new_game(self):
        """Start a new game."""
        if self.llm_adapter._thread and self.llm_adapter._thread.isRunning():
            self.llm_adapter.stop_generation()

        self.board = ChessBoard()
        load_fen(self.board, STARTING_FEN)
        self.move_history.clear()
        self.board_history.clear()
        self.redo_history.clear()
        self._game_over = False
        self._is_ai_turn = False
        
        self.board_updated.emit()
        
        # Check if AI should make the first move
        self._check_ai_turn()

    def set_game_mode(self, white_is_ai: bool, black_is_ai: bool):
        """Set the game mode (human/AI players)."""
        self.white_is_ai = white_is_ai
        self.black_is_ai = black_is_ai
        self._check_ai_turn()

    def set_ai_depth(self, depth: int):
        """Set the AI search depth."""
        self.ai_depth = max(1, min(10, depth))

    def make_move(self, move: Tuple[int, int]) -> bool:
        """Make a move on the board (for human players)."""
        if self._game_over or self._is_ai_turn:
            return False

        legal_moves = generate_legal_moves(self.board)
        if move not in legal_moves:
            print(f"Attempted illegal move: {move}, legal moves are: {legal_moves}")
            return False
            
        # Validate we actually have a piece at the source square
        if self.board.board[move[0]] == '.':
            print(f"Error: No piece at source square {move[0]}, cannot make move {move}")
            return False

        # Save state for undo
        old_state = make_move(self.board, move)
        self.board_history.append((move, old_state))
        self.redo_history.clear()

        # Convert to SAN and add to history
        try:
            san = move_to_san(self.board, move)
            self.move_history.append(san)
        except ValueError as e:
            print(f"Error converting move to SAN: {e}, move={move}, board state at source: {self.board.board[move[0]]}")
            return False

        # Update turn
        if self.board.turn == "w":
            self.board.fullmove_number += 1

        self.move_made.emit(move, san)
        self.board_updated.emit()
        
        # Check for game over
        self._check_game_over()
        
        # Check if AI should move next
        self._check_ai_turn()
        
        return True

    def undo_move(self) -> bool:
        """Undo the last move."""
        if not self.board_history:
            return False

        # If AI is thinking, stop it
        if self._is_ai_turn:
            self.llm_adapter.stop_generation()
            self._is_ai_turn = False
            self.ai_thinking.emit(False)

        # Restore previous state
        move, old_state = self.board_history.pop()
        undo_move(self.board, move, old_state)
        
        if self.move_history:
            self.move_history.pop()
        
        self.redo_history.append((move, old_state))
        self.board_updated.emit()
        return True

    def redo_move(self) -> bool:
        """Redo a previously undone move."""
        if not self.redo_history:
            return False

        if self._is_ai_turn:
            return False

        move, _ = self.redo_history.pop()
        return self.make_move(move)

    def get_current_fen(self) -> str:
        """Get the current position in FEN format."""
        return to_fen(self.board)

    def get_legal_moves(self) -> List[Tuple[int, int]]:
        """Get all legal moves for the current position."""
        return generate_legal_moves(self.board)

    def _check_ai_turn(self):
        """Check if it's the AI's turn to move."""
        if self._game_over:
            return

        current_turn = self.board.turn
        is_ai_turn = ((current_turn == "w" and self.white_is_ai) or
                     (current_turn == "b" and self.black_is_ai))

        if is_ai_turn and not self._is_ai_turn:
            self._is_ai_turn = True
            self.ai_thinking.emit(True)
            # Start AI move generation with a small delay
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, self._start_ai_generation)

    def _start_ai_generation(self):
        """Start the LLM generating a move."""
        if self._game_over:
            return
        self.llm_adapter.start_generation(
            self.board,
            self.move_history.copy(),
            self.ai_depth
        )

    def _on_ai_move_ready(self, move, score, stats):
        """Handle AI move generation completion."""
        self._is_ai_turn = False
        self.ai_thinking.emit(False)

        if move:
            # Make the AI's move
            old_state = make_move(self.board, move)
            self.board_history.append((move, old_state))
            self.redo_history.clear()

            san = move_to_san(self.board, move)
            self.move_history.append(san)

            if self.board.turn == "w":
                self.board.fullmove_number += 1

            self.move_made.emit(move, san)
            self.board_updated.emit()
            
            # Check for game over
            self._check_game_over()
            
            # Check if next player is also AI
            self._check_ai_turn()

    def _on_ai_error(self, error_msg):
        """Handle AI errors."""
        self._is_ai_turn = False
        self.ai_thinking.emit(False)
        self.error_occurred.emit(error_msg)

    def _on_ai_status_changed(self, status):
        """Handle AI status updates."""
        self.ai_status_updated.emit(status)

    def _check_game_over(self):
        """Check if the game has ended."""
        legal_moves = generate_legal_moves(self.board)
        if not legal_moves:
            # Check if it's checkmate or stalemate
            # We'll implement proper king-in-check detection later
            self._game_over = True
            if self.board.turn == "w":
                self.game_over.emit("Checkmate - Black wins!")
            else:
                self.game_over.emit("Checkmate - White wins!")
        elif len(legal_moves) == 0 and self._is_in_check():
            self._game_over = True
            self.game_over.emit("Stalemate!")

    def _is_in_check(self) -> bool:
        """Check if the current player is in check."""
        # Basic implementation - will be expanded
        return False

    def export_pgn(self) -> str:
        """Export the game in PGN format."""
        pgn = [
            '[Event "Chess AI Hybrid Game"]',
            '[Site "Local"]',
            '[Date "??"]',
            '[Round "?"]',
            f'[White "{"AI" if self.white_is_ai else "Human"}"]',
            f'[Black "{"AI" if self.black_is_ai else "Human"}"]',
            '[Result "*"]',
            ''
        ]

        # Add moves in PGN format
        move_text = []
        for i, move in enumerate(self.move_history):
            if i % 2 == 0:
                move_text.append(f"{(i//2)+1}. {move}")
            else:
                move_text.append(move)
        
        if move_text:
            pgn.append(' '.join(move_text))
        
        return '\n'.join(pgn)

    def load_from_fen(self, fen: str):
        """Load a position from FEN."""
        if self.llm_adapter._thread and self.llm_adapter._thread.isRunning():
            self.llm_adapter.stop_generation()

        load_fen(self.board, fen)
        self.move_history.clear()
        self.board_history.clear()
        self.redo_history.clear()
        self._game_over = False
        self._is_ai_turn = False
        self.board_updated.emit()
        self._check_ai_turn()