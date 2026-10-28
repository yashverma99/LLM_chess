"""Game information and controls panel with move history and captured pieces."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QListWidget,
    QListWidgetItem, QHBoxLayout, QPushButton, QComboBox,
    QGroupBox
)
from PySide6.QtCore import Qt, Signal
from gui.styles import PIECE_UNICODE


class GamePanel(QWidget):
    """Panel displaying game information, move history, captured pieces, and controls."""
    
    # Control signals
    new_game_requested = Signal()
    undo_move_requested = Signal()
    redo_move_requested = Signal()
    flip_board_requested = Signal()
    save_game_requested = Signal()
    game_mode_changed = Signal(bool, bool)  # white_is_ai, black_is_ai
    difficulty_changed = Signal(int)  # depth

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(280)
        self.captured_white = []
        self.captured_black = []
        self.setup_ui()

    def setup_ui(self):
        """Set up the game panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Game Status Panel
        self._add_status_panel(layout)
        
        # Captured Pieces
        self._add_captured_panel(layout)
        
        # Move History
        self._add_move_history_panel(layout)
        
        # Game Controls
        self._add_controls_panel(layout)
        
        # Game Mode Selection
        self._add_game_mode_panel(layout)

    def _add_status_panel(self, parent_layout):
        """Add the game status section."""
        frame = QFrame()
        frame.setObjectName("panel")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        frame_layout.setSpacing(12)
        
        # Heading
        heading = QLabel("📊 Game Status")
        heading.setObjectName("heading")
        frame_layout.addWidget(heading)
        
        # Current turn
        self.turn_label = QLabel("Current Turn: White")
        frame_layout.addWidget(self.turn_label)
        
        # Move number
        self.move_number_label = QLabel("Move: 1")
        frame_layout.addWidget(self.move_number_label)
        
        # Game status
        self.game_status_label = QLabel("Status: In Progress")
        frame_layout.addWidget(self.game_status_label)
        
        # Opening name
        self.opening_label = QLabel("Opening: Unknown")
        frame_layout.addWidget(self.opening_label)
        
        parent_layout.addWidget(frame)

    def _add_captured_panel(self, parent_layout):
        """Add the captured pieces section."""
        frame = QFrame()
        frame.setObjectName("panel")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        frame_layout.setSpacing(12)
        
        heading = QLabel("🎯 Captured Pieces")
        heading.setObjectName("heading")
        frame_layout.addWidget(heading)
        
        # White's captured pieces (pieces black captured)
        white_captured_label = QLabel("White's captures:")
        frame_layout.addWidget(white_captured_label)
        self.white_captured_display = QLabel("")
        self.white_captured_display.setStyleSheet("font-size: 24px; min-height: 30px;")
        frame_layout.addWidget(self.white_captured_display)
        
        # Black's captured pieces (pieces white captured)
        black_captured_label = QLabel("Black's captures:")
        frame_layout.addWidget(black_captured_label)
        self.black_captured_display = QLabel("")
        self.black_captured_display.setStyleSheet("font-size: 24px; min-height: 30px;")
        frame_layout.addWidget(self.black_captured_display)
        
        parent_layout.addWidget(frame)

    def _add_move_history_panel(self, parent_layout):
        """Add the move history section."""
        frame = QFrame()
        frame.setObjectName("panel")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        frame_layout.setSpacing(12)
        
        heading = QLabel("📜 Move History")
        heading.setObjectName("heading")
        frame_layout.addWidget(heading)
        
        self.move_history_list = QListWidget()
        self.move_history_list.setMaximumHeight(200)
        frame_layout.addWidget(self.move_history_list)
        
        parent_layout.addWidget(frame)

    def _add_controls_panel(self, parent_layout):
        """Add the game controls section."""
        frame = QFrame()
        frame.setObjectName("panel")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        frame_layout.setSpacing(10)
        
        heading = QLabel("🎮 Controls")
        heading.setObjectName("heading")
        frame_layout.addWidget(heading)
        
        # Button grid layout
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)
        
        # First row
        row1 = QHBoxLayout()
        new_game_btn = QPushButton("New Game")
        new_game_btn.setObjectName("primary")
        new_game_btn.clicked.connect(self.new_game_requested.emit)
        row1.addWidget(new_game_btn)
        
        flip_btn = QPushButton("Flip Board")
        flip_btn.clicked.connect(self.flip_board_requested.emit)
        row1.addWidget(flip_btn)
        btn_layout.addLayout(row1)
        
        # Second row
        row2 = QHBoxLayout()
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.undo_move_requested.emit)
        row2.addWidget(undo_btn)
        
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.redo_move_requested.emit)
        row2.addWidget(redo_btn)
        btn_layout.addLayout(row2)
        
        # Save button
        save_btn = QPushButton("Save PGN")
        save_btn.clicked.connect(self.save_game_requested.emit)
        btn_layout.addWidget(save_btn)
        
        frame_layout.addLayout(btn_layout)
        parent_layout.addWidget(frame)

    def _add_game_mode_panel(self, parent_layout):
        """Add the game mode selection section."""
        frame = QFrame()
        frame.setObjectName("panel")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        frame_layout.setSpacing(12)
        
        heading = QLabel("⚙️ Game Mode")
        heading.setObjectName("heading")
        frame_layout.addWidget(heading)
        
        # Game mode combo
        mode_label = QLabel("Mode:")
        frame_layout.addWidget(mode_label)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Human vs AI",
            "AI vs Human", 
            "Human vs Human",
            "AI vs AI"
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        frame_layout.addWidget(self.mode_combo)
        
        # Difficulty level
        diff_label = QLabel("AI Depth:")
        frame_layout.addWidget(diff_label)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Beginner (1)", "Intermediate (2)", "Advanced (3)", "Expert (4)", "Master (5)"])
        self.difficulty_combo.setCurrentIndex(2)  # Default to advanced (3)
        self.difficulty_combo.currentIndexChanged.connect(self._on_difficulty_changed)
        frame_layout.addWidget(self.difficulty_combo)
        
        parent_layout.addWidget(frame)

    def _on_mode_changed(self, index):
        """Handle game mode selection change."""
        modes = [
            (False, True),   # Human vs AI (white=human, black=ai)
            (True, False),   # AI vs Human (white=ai, black=human)
            (False, False),  # Human vs Human
            (True, True)     # AI vs AI
        ]
        if index < len(modes):
            white_ai, black_ai = modes[index]
            self.game_mode_changed.emit(white_ai, black_ai)

    def _on_difficulty_changed(self, index):
        """Handle difficulty change."""
        depths = [1, 2, 3, 4, 5]
        if index < len(depths):
            self.difficulty_changed.emit(depths[index])

    def update_turn(self, turn: str):
        """Update the current turn display."""
        if turn == "w":
            self.turn_label.setText("Current Turn: White")
        else:
            self.turn_label.setText("Current Turn: Black")

    def update_move_number(self, number: int):
        """Update the move number display."""
        self.move_number_label.setText(f"Move: {number}")

    def update_game_status(self, status: str):
        """Update the game status display."""
        self.game_status_label.setText(f"Status: {status}")

    def add_move_to_history(self, move_number: int, white_move: str, black_move: str = None):
        """Add a move pair to the history."""
        if black_move:
            item_text = f"{move_number}. {white_move} {black_move}"
        else:
            item_text = f"{move_number}. {white_move}"
        item = QListWidgetItem(item_text)
        self.move_history_list.addItem(item)

    def clear_move_history(self):
        """Clear the move history display."""
        self.move_history_list.clear()

    def add_captured_piece(self, piece: str):
        """Add a captured piece to the display."""
        if piece.isupper():  # White piece captured by black
            self.captured_black.append(piece)
            self._update_captured_display()
        else:  # Black piece captured by white
            self.captured_white.append(piece)
            self._update_captured_display()

    def _update_captured_display(self):
        """Update the captured pieces display."""
        white_text = ''.join([PIECE_UNICODE[p] for p in self.captured_white])
        black_text = ''.join([PIECE_UNICODE[p] for p in self.captured_black])
        self.white_captured_display.setText(white_text)
        self.black_captured_display.setText(black_text)

    def reset_captured_pieces(self):
        """Reset captured pieces for new game."""
        self.captured_white.clear()
        self.captured_black.clear()
        self._update_captured_display()

    def reset_for_new_game(self):
        """Reset all game info for a new game."""
        self.update_turn("w")
        self.update_move_number(1)
        self.update_game_status("In Progress")
        self.clear_move_history()
        self.reset_captured_pieces()