"""LLM Adapter for the chess GUI - wraps existing LSTM implementation."""
from PySide6.QtCore import QObject, Signal, QThread
from typing import Optional, Tuple, Dict, Any
from engine.hybrid import find_hybrid_move
from engine.board import ChessBoard
from engine.legal_moves import generate_legal_moves, make_move, undo_move
from engine.fen import to_fen


class LLMWorker(QObject):
    """Background worker that runs the LLM move generation."""
    move_generated = Signal(object, float, dict)  # move, score, stats
    error_occurred = Signal(str)
    thinking_update = Signal(str)

    def __init__(self):
        super().__init__()
        self._board = None
        self._history = None
        self._depth = 3
        self._should_stop = False

    def set_parameters(self, board: ChessBoard, history: list, depth: int = 3):
        """Set the parameters for the next move generation."""
        self._board = board
        self._history = history
        self._depth = depth
        self._should_stop = False

    def stop(self):
        """Stop any ongoing computation."""
        self._should_stop = True

    def generate_move(self):
        """Generate a move using the existing LLM implementation."""
        if not self._board or self._should_stop:
            return

        try:
            self.thinking_update.emit("Analyzing position...")
            legal_moves = generate_legal_moves(self._board)
            
            if not legal_moves:
                self.error_occurred.emit("No legal moves available")
                return

            self.thinking_update.emit("Running LSTM evaluation...")
            move, score, stats = find_hybrid_move(
                self._board,
                history=self._history,
                depth=self._depth
            )

            if self._should_stop:
                return

            try:
                if move and move in legal_moves:
                    self.move_generated.emit(move, score, stats)
                else:
                    if legal_moves:
                        # Fallback to first legal move if LLM failed
                        print(f"LLM did not return a valid move, using first legal move: {legal_moves[0]}")
                        self.move_generated.emit(legal_moves[0], 0.0, {
                            "mode": "fallback",
                            "reason": "LLM did not return a valid legal move"
                        })
                    else:
                        self.error_occurred.emit("No valid move could be generated")
            except Exception as e:
                print(f"Error in move processing, using fallback: {e}")
                if legal_moves:
                    self.move_generated.emit(legal_moves[0], 0.0, {
                        "mode": "fallback",
                        "reason": f"Exception: {str(e)}"
                    })
                else:
                    self.error_occurred.emit(f"No valid move could be generated: {str(e)}")

        except Exception as e:
            if not self._should_stop:
                self.error_occurred.emit(f"LLM error: {str(e)}")


class LLMAdapter(QObject):
    """Adapter that manages the LLM worker thread and provides a clean API."""
    move_ready = Signal(object, float, dict)  # move, score, stats
    error = Signal(str)
    status_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._thread = None
        self._worker = None
        self._max_retries = 3
        self._retry_count = 0

    def start_generation(self, board: ChessBoard, history: list, depth: int = 3):
        """Start generating a move in the background."""
        if self._thread and self._thread.isRunning():
            self.stop_generation()

        # Create new thread and worker
        self._thread = QThread()
        self._worker = LLMWorker()
        self._worker.moveToThread(self._thread)

        # Connect signals
        self._thread.started.connect(self._worker.generate_move)
        self._worker.move_generated.connect(self._on_move_generated)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.thinking_update.connect(self.status_changed)

        # Set parameters
        self._worker.set_parameters(board, history, depth)
        self._retry_count = 0

        # Start the thread
        self._thread.start()
        self.status_changed.emit("AI is thinking...")

    def stop_generation(self):
        """Stop any ongoing move generation."""
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(3000)  # Wait up to 3 seconds
            if self._thread.isRunning():
                self._thread.terminate()
                self._thread.wait()

    def _on_move_generated(self, move, score, stats):
        """Handle a successfully generated move."""
        self._cleanup()
        self._retry_count = 0
        self.move_ready.emit(move, score, stats)

    def _on_error(self, error_msg):
        """Handle an error in move generation."""
        self._cleanup()
        self._retry_count += 1
        
        if self._retry_count < self._max_retries:
            self.status_changed.emit(f"Retrying... ({self._retry_count}/{self._max_retries})")
            # Could implement retry logic here
            self.error.emit(f"Retry {self._retry_count}: {error_msg}")
        else:
            self.error.emit(f"Failed after {self._max_retries} attempts: {error_msg}")

    def _cleanup(self):
        """Clean up thread and worker."""
        if self._thread:
            self._thread.quit()
            self._thread.wait()
        self._thread = None
        self._worker = None

    def __del__(self):
        """Ensure thread is cleaned up."""
        self.stop_generation()