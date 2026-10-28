"""Interactive chessboard widget using PySide6."""
from PySide6.QtWidgets import QWidget, QSizePolicy, QApplication
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QFont, QMouseEvent, QPaintEvent
from PySide6.QtCore import Qt, Signal, QRect, QSize
from gui.styles import COLORS, PIECE_UNICODE
from engine.board import ChessBoard
from engine.fen import load_fen
from engine.legal_moves import generate_legal_moves


class ChessBoardWidget(QWidget):
    """Interactive chessboard widget that displays and handles input for the chess game."""
    
    square_clicked = Signal(int, int)  # file, rank (0-7, 0-7 from white's perspective)
    move_selected = Signal(tuple)  # (from_index, to_index)

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(400, 400)
        
        # Board state
        self.board = ChessBoard()
        load_fen(self.board, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        
        # Selection state
        self.selected_square: tuple = None  # (file, rank)
        self.legal_moves: list = []  # list of (from, to) index tuples
        self.last_move: tuple = None  # (from_index, to_index)
        self.flip_board = False  # Whether to flip the board for black's perspective
        
        # Styling
        self.square_size = 50
        self.board_offset = 20
        self.padding = 10
        
        # Colors
        self.white_color = QColor(COLORS['white_square'])
        self.black_color = QColor(COLORS['black_square'])
        self.selected_color = QColor(COLORS['selected'])
        self.legal_move_color = QColor(COLORS['legal_move'])
        self.last_move_color = QColor(COLORS['last_move'])
        self.check_color = QColor(COLORS['check'])
        
        # Enable mouse tracking
        self.setMouseTracking(True)

    def update_board(self, board: ChessBoard, legal_moves=None):
        """Update the internal board state and trigger repaint."""
        self.board = board
        if legal_moves is not None:
            self.legal_moves = legal_moves
        self.update()

    def set_selected_square(self, file: int, rank: int):
        """Set the currently selected square."""
        self.selected_square = (file, rank)
        self.update()

    def clear_selection(self):
        """Clear the current selection."""
        self.selected_square = None
        self.update()

    def set_last_move(self, from_index: int, to_index: int):
        """Highlight the last move made."""
        self.last_move = (from_index, to_index)
        self.update()

    def set_flip_board(self, flip: bool):
        """Set whether the board is flipped."""
        self.flip_board = flip
        self.update()

    def sizeHint(self) -> QSize:
        """Suggested size for the widget."""
        return QSize(600, 600)

    def resizeEvent(self, event):
        """Handle widget resizing to maintain square board."""
        super().resizeEvent(event)
        available_size = min(self.width(), self.height()) - 2 * self.board_offset
        self.square_size = available_size // 8
        self.update()

    def paintEvent(self, event: QPaintEvent):
        """Paint the chessboard and pieces."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(COLORS['background']))
        
        # Draw the board squares
        board_start_x = (self.width() - 8 * self.square_size) // 2
        board_start_y = (self.height() - 8 * self.square_size) // 2
        
        # Draw board border
        painter.setPen(QPen(QColor(COLORS['border']), 3))
        painter.drawRect(
            board_start_x - 2, 
            board_start_y - 2, 
            8 * self.square_size + 4, 
            8 * self.square_size + 4
        )
        
        for rank in range(8):
            for file in range(8):
                # Calculate screen coordinates (account for board flipping)
                if self.flip_board:
                    display_rank = 7 - rank
                    display_file = 7 - file
                else:
                    display_rank = rank
                    display_file = file
                    
                x = board_start_x + display_file * self.square_size
                y = board_start_y + display_rank * self.square_size
                
                # Determine square color
                if (rank + file) % 2 == 0:
                    color = self.white_color
                else:
                    color = self.black_color
                
                # Check if this square is selected
                if self.selected_square == (file, rank):
                    color = self.selected_color
                # Check if this square is part of the last move
                elif self.last_move:
                    from_idx = self.last_move[0]
                    to_idx = self.last_move[1]
                    current_idx = rank * 8 + file
                    if current_idx == from_idx or current_idx == to_idx:
                        color = self.last_move_color
                # Check if this square is a legal move destination
                else:
                    for move in self.legal_moves:
                        if len(move) >= 2 and isinstance(move[0], int) and isinstance(move[1], int):
                            # If legal_moves contains (file, rank) widget coordinates
                            if move[0] == file and move[1] == rank:
                                color = self.legal_move_color
                                break
                        elif isinstance(move, int):
                            # If legal_moves contains index values (old format)
                            current_idx = rank * 8 + file
                            if current_idx == move:
                                color = self.legal_move_color
                                break
                
                # Draw the square
                painter.fillRect(x, y, self.square_size, self.square_size, color)
                
                # Draw the piece if there is one
                index = rank * 8 + file
                piece = self.board.board[index]
                if piece != '.':
                    self._draw_piece(painter, piece, x, y)
        
        # Draw file labels (a-h)
        painter.setPen(QColor(COLORS['text_secondary']))
        font = QFont('Segoe UI', 10)
        painter.setFont(font)
        
        for file in range(8):
            display_file = 7 - file if self.flip_board else file
            label = chr(ord('a') + file)
            x = board_start_x + display_file * self.square_size + self.square_size // 2
            y = board_start_y + 8 * self.square_size + 15
            painter.drawText(x - 5, y, label)
        
        # Draw rank labels (1-8)
        for rank in range(8):
            display_rank = 7 - rank if self.flip_board else rank
            label = str(8 - rank)
            x = board_start_x - 15
            y = board_start_y + display_rank * self.square_size + self.square_size // 2 + 5
            painter.drawText(x, y, label)

    def _draw_piece(self, painter: QPainter, piece: str, x: int, y: int):
        """Draw a chess piece on the board."""
        # Set text color based on piece color
        if piece.isupper():  # White pieces
            painter.setPen(QColor('#ffffff'))
            text_color = QColor('#ffffff')
        else:  # Black pieces
            painter.setPen(QColor('#000000'))
            text_color = QColor('#000000')
        
        # Create a drop shadow effect
        painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
        
        # Draw the piece with a large font
        font = QFont('Arial Unicode MS', int(self.square_size * 0.7))
        painter.setFont(font)
        
        # Calculate center position
        piece_char = PIECE_UNICODE.get(piece, '')
        if piece_char:
            # Draw with small offset for shadow
            painter.drawText(x + 3, y + self.square_size - 10, piece_char)
            painter.setPen(QColor(text_color))
            painter.drawText(x, y + self.square_size - 13, piece_char)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse clicks on the board."""
        if event.button() == Qt.LeftButton:
            board_start_x = (self.width() - 8 * self.square_size) // 2
            board_start_y = (self.height() - 8 * self.square_size) // 2
            
            # Convert click position to board coordinates
            click_x = event.position().x() - board_start_x
            click_y = event.position().y() - board_start_y
            
            if 0 <= click_x < 8 * self.square_size and 0 <= click_y < 8 * self.square_size:
                file = int(click_x // self.square_size)
                rank = int(click_y // self.square_size)
                
                # Convert to logical coordinates accounting for flip
                if self.flip_board:
                    logical_file = 7 - file
                    logical_rank = 7 - rank
                else:
                    logical_file = file
                    logical_rank = rank
                
                index = logical_rank * 8 + logical_file
                self.square_clicked.emit(logical_file, logical_rank)
                
                # Emit square clicked signal
                super().mousePressEvent(event)