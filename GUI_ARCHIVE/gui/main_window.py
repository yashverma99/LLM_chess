"""Main application window that integrates all GUI components."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter, 
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from gui.chess_board_widget import ChessBoardWidget
from gui.analysis_panel import AnalysisPanel
from gui.chat_panel import ChatPanel
from gui.game_panel import GamePanel
from gui.styles import STYLESHEET
from engine.game_controller import GameController
from engine.fen import to_fen
import json
from pathlib import Path


class MainWindow(QMainWindow):
    """Main application window for the chess AI GUI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess AI Hybrid")
        self.setMinimumSize(1400, 900)
        
        # Game controller (manages the chess engine and AI)
        self.game_controller = GameController()
        
        # Setup UI
        self.setup_ui()
        self.connect_signals()
        
        # Selection tracking
        self.selected_square_index = None
        
        # Set default game mode: Human (white) vs AI (black)
        self.game_controller.set_game_mode(white_is_ai=False, black_is_ai=True)

    def setup_ui(self):
        """Set up the main window UI with all panels."""
        # Apply stylesheet
        self.setStyleSheet(STYLESHEET)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStretchFactor(1, 1)  # Chessboard gets all extra space
        
        # Left panel: Analysis and Chat (tabbed or stacked)
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center: Chessboard
        self.chess_board_widget = ChessBoardWidget()
        splitter.addWidget(self.chess_board_widget)
        
        # Right panel: Game info, history, controls
        self.game_panel = GamePanel()
        splitter.addWidget(self.game_panel)
        
        # Set reasonable default sizes
        splitter.setSizes([350, 600, 320])
        
        main_layout.addWidget(splitter)

    def _create_left_panel(self):
        """Create the left panel containing analysis and chat."""
        from PySide6.QtWidgets import QTabWidget
        left_tabwidget = QTabWidget()
        left_tabwidget.setMinimumWidth(320)
        
        # Analysis tab
        self.analysis_panel = AnalysisPanel()
        left_tabwidget.addTab(self.analysis_panel, "🧠 Analysis")
        
        # Chat tab
        self.chat_panel = ChatPanel()
        left_tabwidget.addTab(self.chat_panel, "💬 Chat")
        
        return left_tabwidget

    def connect_signals(self):
        """Connect all signals between components."""
        # Chessboard interactions
        self.chess_board_widget.square_clicked.connect(self.on_square_clicked)
        
        # Game controller signals
        self.game_controller.board_updated.connect(self.on_board_updated)
        self.game_controller.move_made.connect(self.on_move_made)
        self.game_controller.game_over.connect(self.on_game_over)
        self.game_controller.ai_thinking.connect(self.on_ai_thinking)
        self.game_controller.ai_status_updated.connect(self.on_ai_status_updated)
        self.game_controller.error_occurred.connect(self.on_error)
        
        # Game panel control signals
        self.game_panel.new_game_requested.connect(self.on_new_game)
        self.game_panel.undo_move_requested.connect(self.on_undo_move)
        self.game_panel.redo_move_requested.connect(self.on_redo_move)
        self.game_panel.flip_board_requested.connect(self.on_flip_board)
        self.game_panel.save_game_requested.connect(self.on_save_game)
        self.game_panel.game_mode_changed.connect(self.on_game_mode_changed)
        self.game_panel.difficulty_changed.connect(self.on_difficulty_changed)
        
        # Chat panel signals
        self.chat_panel.message_sent.connect(self.on_chat_message)

    def on_square_clicked(self, file: int, rank: int):
        """Handle when a square on the chessboard is clicked."""
        # Convert file/rank (0-7, 0-7, where rank 0 is white's home rank in widget) to board index 
        # In our board, rank 0 is black's home rank, so we need to invert the rank
        widget_rank = rank  # 0 is bottom (white's back rank) in the widget
        board_rank = 7 - widget_rank  # invert to match board's coordinate system (0=black's back rank)
        index = board_rank * 8 + file
        print(f"Clicked square file={file}, widget_rank={widget_rank}, board_rank={board_rank}, index={index}, piece={self.game_controller.board.board[index]}")
        print(f"Current turn: {self.game_controller.board.turn}")
        print(f"AI turn status: {self.game_controller._is_ai_turn}")
        
        # Don't allow moves if it's the AI's turn
        if self.game_controller._is_ai_turn:
            print("Cannot move - it's the AI's turn!")
            return
            
        if self.selected_square_index is None:
            # First click - select the square only if it's a piece of the current turn
            piece = self.game_controller.board.board[index]
            if piece != '.':  # Only select if there's a piece
                piece_color = 'w' if piece.isupper() else 'b'
                if piece_color == self.game_controller.board.turn:
                    print(f"Selected piece {piece} at index {index}")
                    self.selected_square_index = index
                    # Convert back to widget coordinates for highlighting
                    selected_widget_rank = 7 - (index // 8)
                    selected_file = index % 8
                    self.chess_board_widget.set_selected_square(selected_file, selected_widget_rank)
                    
                    # Get legal moves from this square
                    legal_moves = self.game_controller.get_legal_moves()
                    print(f"All legal moves: {legal_moves}")
                    moves_from_here = [m for m in legal_moves if m[0] == index]
                    print(f"Legal moves from here: {moves_from_here}")
                    
                    # Convert legal moves to widget coordinates
                    widget_legal_moves = []
                    for (start, end) in moves_from_here:
                        end_board_rank = end // 8
                        end_widget_rank = 7 - end_board_rank
                        end_file = end % 8
                        widget_legal_moves.append((end_file, end_widget_rank))
                    
                    self.chess_board_widget.legal_moves = widget_legal_moves
                    self.chess_board_widget.update()
        else:
            # Second click - check if we're clicking on another of our own pieces
            piece = self.game_controller.board.board[index]
            if piece != '.':
                piece_color = 'w' if piece.isupper() else 'b'
                if piece_color == self.game_controller.board.turn:
                    # Switch selection to this new piece
                    print(f"Switching selection to new piece {piece} at index {index}")
                    self.selected_square_index = index
                    selected_widget_rank = 7 - (index // 8)
                    selected_file = index % 8
                    self.chess_board_widget.set_selected_square(selected_file, selected_widget_rank)
                    legal_moves = self.game_controller.get_legal_moves()
                    moves_from_here = [m for m in legal_moves if m[0] == index]
                    
                    # Convert to widget coordinates
                    widget_legal_moves = []
                    for (start, end) in moves_from_here:
                        end_board_rank = end // 8
                        end_widget_rank = 7 - end_board_rank
                        end_file = end % 8
                        widget_legal_moves.append((end_file, end_widget_rank))
                    
                    self.chess_board_widget.legal_moves = widget_legal_moves
                    self.chess_board_widget.update()
                    return
            
            # Only attempt to make a move if we're clicking on a legal destination
            legal_moves = self.game_controller.get_legal_moves()
            attempted_move = (self.selected_square_index, index)
            print(f"Attempting move: {attempted_move}")
            print(f"Is in legal moves? {attempted_move in legal_moves}")
            
            if attempted_move in legal_moves:
                print(f"Making legal move: {attempted_move}")
                success = self.game_controller.make_move(attempted_move)
                print(f"Move successful: {success}")
            else:
                print(f"Illegal move attempted: {attempted_move}")
            
            # Clear selection regardless
            self.selected_square_index = None
            self.chess_board_widget.clear_selection()
            self.chess_board_widget.legal_moves = []
            self.chess_board_widget.update()

    def on_board_updated(self):
        """Handle board state updates."""
        legal_moves = self.game_controller.get_legal_moves()
        self.chess_board_widget.update_board(self.game_controller.board, legal_moves)
        
        # Update turn display
        self.game_panel.update_turn(self.game_controller.board.turn)
        self.game_panel.update_move_number(self.game_controller.board.fullmove_number)

    def on_move_made(self, move, san):
        """Handle a move being successfully made."""
        # Update last move highlight
        self.chess_board_widget.set_last_move(move[0], move[1])
        
        # Add to move history display
        if len(self.game_controller.move_history) % 2 == 1:
            # White's move - add as single
            move_num = (len(self.game_controller.move_history) + 1) // 2
            self.game_panel.add_move_to_history(move_num, san)
        else:
            # Black's move - update the last entry
            last_item = self.game_panel.move_history_list.item(self.game_panel.move_history_list.count() - 1)
            if last_item:
                text = last_item.text()
                new_text = f"{text} {san}"
                last_item.setText(new_text)
        
        # Check for captured pieces
        captured_piece = self.game_controller.board.board[move[1]]
        if captured_piece != '.':
            self.game_panel.add_captured_piece(captured_piece)
        
        # Update analysis panel with move info
        self.analysis_panel.update_last_move(san, 0.0)
        
        # Clear selection
        self.selected_square_index = None
        self.chess_board_widget.clear_selection()

    def on_game_over(self, reason):
        """Handle game over state."""
        self.game_panel.update_game_status(reason)
        QMessageBox.information(self, "Game Over", reason)

    def on_ai_thinking(self, is_thinking):
        """Update UI when AI starts/stops thinking."""
        self.analysis_panel.set_thinking(is_thinking)

    def on_ai_status_updated(self, status):
        """Update AI status display."""
        self.analysis_panel.update_status(status)

    def on_error(self, error_msg):
        """Handle errors from the game controller."""
        QMessageBox.warning(self, "Error", error_msg)

    def on_new_game(self):
        """Start a new game."""
        # Confirm with user
        reply = QMessageBox.question(
            self, "New Game", 
            "Are you sure you want to start a new game? Current progress will be lost.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.game_controller.new_game()
            self.analysis_panel.clear_analysis()
            self.chat_panel.clear_chat()
            self.game_panel.reset_for_new_game()
            self.selected_square_index = None

    def on_undo_move(self):
        """Undo the last move."""
        if self.game_controller.undo_move():
            self.chess_board_widget.clear_selection()
            self.selected_square_index = None
            # Update move history display - could implement full undo, but for simplicity just refresh

    def on_redo_move(self):
        """Redo a previously undone move."""
        self.game_controller.redo_move()

    def on_flip_board(self):
        """Flip the chessboard."""
        current_flip = self.chess_board_widget.flip_board
        self.chess_board_widget.set_flip_board(not current_flip)

    def on_save_game(self):
        """Save the current game as PGN."""
        pgn = self.game_controller.export_pgn()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PGN", "", "PGN Files (*.pgn);;All Files (*.*)"
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(pgn)
            QMessageBox.information(self, "Game Saved", f"PGN saved to:\n{file_path}")

    def on_game_mode_changed(self, white_is_ai, black_is_ai):
        """Update game mode when changed in UI."""
        self.game_controller.set_game_mode(white_is_ai, black_is_ai)

    def on_difficulty_changed(self, depth):
        """Update AI search depth."""
        self.game_controller.set_ai_depth(depth)

    def on_chat_message(self, message: str):
        """Handle user chat messages, generate AI responses."""
        # Use the LLM to generate a response with the current board context
        current_fen = self.game_controller.get_current_fen()
        move_history = self.game_controller.move_history.copy()
        
        # Generate context-aware response
        response = self._generate_ai_response(message, current_fen, move_history)
        self.chat_panel.add_ai_message(response)

    def _generate_ai_response(self, user_message: str, fen: str, history: list) -> str:
        """Generate an AI response to a chat query using the LLM context."""
        # This would integrate with your LLM to generate real responses
        # For now, provide context-aware template responses
        
        if "evaluation" in user_message.lower() or "what do you think" in user_message.lower():
            return f"Looking at the current position (FEN: {fen[:30]}...), the position is relatively balanced. The material count is equal, and both players have good development. I'd rate this position as roughly equal with a slight edge to white due to better central control."
        
        elif "why did you" in user_message.lower():
            if history:
                last_move = history[-1]
                return f"My last move {last_move} was chosen to develop my pieces and control central squares. It prepares future attacking opportunities while maintaining solid defensive structure. The LSTM model ranked this as the highest-probability move in this position."
            else:
                return "No moves have been made yet! I'll explain my reasoning once I've played a move."
        
        elif "what should i do" in user_message.lower() or "suggest" in user_message.lower():
            legal_moves = self.game_controller.get_legal_moves()
            if legal_moves:
                return f"You have {len(legal_moves)} legal moves in this position. I'd recommend focusing on central control and piece development. Developing a knight or central pawn would be strongest here."
            return "The game appears to be over."
        
        elif "opening" in user_message.lower():
            if len(history) < 3:
                return "This looks like it could be developing into a standard opening. Common openings in this position include the Italian Game, Spanish Game (Ruy Lopez), or Sicilian Defense depending on how play continues."
            else:
                return "Based on the first few moves, we're in a standard opening position. Both players have focused on central control, which is the correct approach in the opening phase."
        
        else:
            return f"I've analyzed the current position (FEN: {fen[:40]}...). With {len(history)} moves played so far, the game is progressing normally. Feel free to ask me specific questions about tactics, strategy, or my decision-making process!"