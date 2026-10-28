"""AI chat panel for interacting with the LLM about the chess position."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QTextEdit, 
    QLineEdit, QPushButton, QScrollArea, QWidget as QWidgetScroll
)
from PySide6.QtCore import Qt, Signal
from datetime import datetime


class ChatMessageWidget(QFrame):
    """Widget that displays a single chat message."""
    
    def __init__(self, message: str, is_ai: bool = False):
        super().__init__()
        self.setObjectName("panel")
        self.setStyleSheet("margin: 4px; padding: 8px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Sender label
        sender = QLabel("🤖 AI" if is_ai else "👤 You")
        sender.setStyleSheet("font-weight: 600; font-size: 12px; color: #22c55e;" if is_ai else 
                           "font-weight: 600; font-size: 12px; color: #94a3b8;")
        layout.addWidget(sender)
        
        # Message text
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("margin-top: 4px; line-height: 1.4;")
        layout.addWidget(message_label)
        
        # Timestamp
        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setStyleSheet("font-size: 10px; color: #64748b; margin-top: 4px;")
        layout.addWidget(time_label)


class ChatPanel(QWidget):
    """Panel that provides an interactive chat interface with the AI."""
    
    message_sent = Signal(str)  # Signal emitted when user sends a message

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(300)
        self.setup_ui()

    def setup_ui(self):
        """Set up the chat panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Main frame
        frame = QFrame()
        frame.setObjectName("panel")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        frame_layout.setSpacing(12)
        
        # Heading
        heading = QLabel("💬 AI Chat")
        heading.setObjectName("heading")
        frame_layout.addWidget(heading)
        
        # Description
        desc = QLabel("Ask the AI about the current position, strategy, or to explain moves.")
        desc.setStyleSheet("color: #94a3b8; font-size: 12px;")
        frame_layout.addWidget(desc)
        
        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")
        
        # Container widget for messages
        self.messages_container = QWidgetScroll()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(8)
        self.scroll_area.setWidget(self.messages_container)
        
        frame_layout.addWidget(self.scroll_area)
        
        # Quick questions
        quick_label = QLabel("Quick questions:")
        quick_label.setStyleSheet("font-size: 11px; color: #94a3b8; margin-top: 8px;")
        frame_layout.addWidget(quick_label)
        
        # Quick question buttons
        self._add_quick_buttons(frame_layout)
        
        # Message input area
        input_layout = QVBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Ask the AI a question...")
        self.message_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_input)
        
        send_btn = QPushButton("Send")
        send_btn.setObjectName("primary")
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        
        frame_layout.addLayout(input_layout)
        layout.addWidget(frame)
        
        # Add welcome message
        self.add_ai_message("Hello! I'm your chess AI assistant. I can analyze positions, explain my moves, and suggest strategies. Ask me anything about the current game!")

    def _add_quick_buttons(self, layout):
        """Add quick question buttons."""
        questions = [
            "What is your evaluation of this position?",
            "Why did you choose that last move?",
            "What should I do next?",
            "What is the opening being played?"
        ]
        
        for question in questions:
            btn = QPushButton(question)
            btn.setStyleSheet("text-align: left; padding: 6px 10px; font-size: 11px;")
            btn.clicked.connect(lambda checked, q=question: self._send_quick_question(q))
            layout.addWidget(btn)

    def _send_quick_question(self, question: str):
        """Handle quick question button click."""
        self.add_user_message(question)
        self.message_sent.emit(question)

    def _send_message(self):
        """Send the user's typed message."""
        message = self.message_input.text().strip()
        if message:
            self.add_user_message(message)
            self.message_sent.emit(message)
            self.message_input.clear()

    def add_user_message(self, message: str):
        """Add a user message to the chat."""
        widget = ChatMessageWidget(message, is_ai=False)
        self.messages_layout.addWidget(widget)
        self._scroll_to_bottom()

    def add_ai_message(self, message: str):
        """Add an AI message to the chat."""
        widget = ChatMessageWidget(message, is_ai=True)
        self.messages_layout.addWidget(widget)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """Scroll the chat area to the bottom."""
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def clear_chat(self):
        """Clear all chat messages for a new game."""
        # Remove all message widgets
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Add welcome back message
        self.add_ai_message("New game started! I'm ready to analyze our new match.")