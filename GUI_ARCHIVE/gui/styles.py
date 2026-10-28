"""Premium dark theme styles for the chess GUI."""

# Color palette - premium dark theme with green accents
COLORS = {
    "background": "#0f172a",
    "surface": "#1e293b",
    "surface_hover": "#334155",
    "border": "#334155",
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",
    "accent": "#22c55e",      # Emerald green
    "accent_hover": "#16a34a",
    "accent_light": "#4ade80",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "white_square": "#f1f5f9",
    "black_square": "#64748b",
    "selected": "#22c55e",
    "legal_move": "#86efac",
    "last_move": "#fcd34d",
    "check": "#ef4444",
}

# Main application stylesheet
STYLESHEET = f"""
/* Global styles */
QMainWindow {{
    background-color: {COLORS['background']};
}}

QWidget {{
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
}}

/* Panel styling */
QFrame#panel {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}

QFrame#panel:hover {{
    border-color: {COLORS['accent']};
}}

/* Button styling */
QPushButton {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {COLORS['surface_hover']};
    border-color: {COLORS['accent']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent']};
}}

QPushButton:disabled {{
    opacity: 0.5;
    background-color: {COLORS['surface']};
    border-color: {COLORS['border']};
}}

/* Primary accent button */
QPushButton#primary {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent']};
}}

QPushButton#primary:hover {{
    background-color: {COLORS['accent_hover']};
}}

/* Text input styling */
QLineEdit, QTextEdit {{
    background-color: {COLORS['background']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}}

QLineEdit:focus, QTextEdit:focus {{
    border-color: {COLORS['accent']};
    outline: none;
}}

/* Label styling */
QLabel {{
    font-size: 13px;
}}

QLabel#heading {{
    font-size: 18px;
    font-weight: 600;
    color: {COLORS['text_primary']};
}}

QLabel#subheading {{
    font-size: 14px;
    font-weight: 500;
    color: {COLORS['text_secondary']};
}}

QLabel#status {{
    font-size: 12px;
    color: {COLORS['accent']};
}}

/* Scrollbar styling */
QScrollBar:vertical {{
    background-color: {COLORS['background']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['accent']};
}}

/* ComboBox styling */
QComboBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {COLORS['accent']};
}}

QComboBox::drop-down {{
    border: none;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}

/* List widget for move history */
QListWidget {{
    background-color: {COLORS['background']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}

QListWidget::item {{
    padding: 4px 8px;
    border-bottom: 1px solid {COLORS['border']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['accent']};
    color: white;
}}

/* Loading animation label */
QLabel#thinking {{
    color: {COLORS['accent']};
    font-style: italic;
}}
"""

# Chess piece Unicode characters for rendering (we'll use these until we add proper images)
PIECE_UNICODE = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    '.': ''
}

# Map your engine's piece notation to readable names
PIECE_NAMES = {
    'K': 'White King', 'Q': 'White Queen', 'R': 'White Rook',
    'B': 'White Bishop', 'N': 'White Knight', 'P': 'White Pawn',
    'k': 'Black King', 'q': 'Black Queen', 'r': 'Black Rook',
    'b': 'Black Bishop', 'n': 'Black Knight', 'p': 'Black Pawn'
}