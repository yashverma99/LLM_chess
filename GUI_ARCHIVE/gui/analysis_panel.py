"""AI analysis panel widget showing LLM thinking status and analysis."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QProgressBar,
    QTextEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class AnalysisPanel(QWidget):
    """Panel that displays AI thinking, analysis, and move information."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(300)
        self.setup_ui()
        
        # Thinking animation
        self.thinking_timer = QTimer()
        self.thinking_timer.timeout.connect(self._update_thinking_animation)
        self.thinking_dots = 0
        self.is_thinking = False

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Main panel frame
        frame = QFrame()
        frame.setObjectName("panel")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        frame_layout.setSpacing(16)
        
        # Heading
        heading = QLabel("🧠 AI Analysis")
        heading.setObjectName("heading")
        frame_layout.addWidget(heading)
        
        # AI Status section
        status_label = QLabel("Current Status")
        status_label.setObjectName("subheading")
        frame_layout.addWidget(status_label)
        
        self.status_text = QLabel("Ready")
        self.status_text.setObjectName("status")
        frame_layout.addWidget(self.status_text)
        
        # Thinking progress indicator
        self.thinking_label = QLabel("")
        self.thinking_label.setObjectName("thinking")
        self.thinking_label.hide()
        frame_layout.addWidget(self.thinking_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()
        frame_layout.addWidget(self.progress_bar)
        
        # Last move analysis
        last_move_label = QLabel("Last Move")
        last_move_label.setObjectName("subheading")
        frame_layout.addWidget(last_move_label)
        
        self.last_move_text = QLabel("No moves yet")
        frame_layout.addWidget(self.last_move_text)
        
        # Move statistics
        stats_label = QLabel("Engine Statistics")
        stats_label.setObjectName("subheading")
        frame_layout.addWidget(stats_label)
        
        self.stats_list = QListWidget()
        self.stats_list.setMaximumHeight(150)
        frame_layout.addWidget(self.stats_list)
        
        # AI Explanation section
        explanation_label = QLabel("AI Explanation")
        explanation_label.setObjectName("subheading")
        frame_layout.addWidget(explanation_label)
        
        self.explanation_text = QTextEdit()
        self.explanation_text.setPlaceholderText("AI explanations will appear here...")
        self.explanation_text.setMaximumHeight(120)
        self.explanation_text.setReadOnly(True)
        frame_layout.addWidget(self.explanation_text)
        
        # Position evaluation
        eval_label = QLabel("Position Evaluation")
        eval_label.setObjectName("subheading")
        frame_layout.addWidget(eval_label)
        
        self.evaluation_bar = QProgressBar()
        self.evaluation_bar.setRange(-1000, 1000)
        self.evaluation_bar.setValue(0)
        self.evaluation_bar.setTextVisible(True)
        self.evaluation_bar.setFormat("%.2f" % 0)
        frame_layout.addWidget(self.evaluation_bar)
        
        # Candidate moves
        candidates_label = QLabel("Top Candidate Moves")
        candidates_label.setObjectName("subheading")
        frame_layout.addWidget(candidates_label)
        
        self.candidates_list = QListWidget()
        self.candidates_list.setMaximumHeight(100)
        frame_layout.addWidget(self.candidates_list)
        
        layout.addWidget(frame)
        self.setLayout(layout)

    def set_thinking(self, is_thinking: bool):
        """Update the UI to show that the AI is thinking."""
        self.is_thinking = is_thinking
        if is_thinking:
            self.thinking_label.show()
            self.progress_bar.show()
            self.status_text.setText("AI is calculating...")
            self.thinking_timer.start(500)
        else:
            self.thinking_label.hide()
            self.progress_bar.hide()
            self.thinking_timer.stop()
            self.status_text.setText("Ready")
            self.thinking_dots = 0

    def update_status(self, status: str):
        """Update the status text."""
        self.status_text.setText(status)

    def _update_thinking_animation(self):
        """Update the thinking animation dots."""
        self.thinking_dots = (self.thinking_dots + 1) % 4
        dots = '.' * self.thinking_dots
        self.thinking_label.setText(f"Thinking{dots}")

    def update_last_move(self, san_move: str, score: float):
        """Update the last move displayed."""
        self.last_move_text.setText(f"Played: {san_move} (score: {score:.2f})")

    def update_statistics(self, stats: dict):
        """Update the engine statistics display."""
        self.stats_list.clear()
        for key, value in stats.items():
            item = QListWidgetItem(f"{key}: {value}")
            self.stats_list.addItem(item)

    def update_evaluation(self, score: float):
        """Update the position evaluation bar."""
        # Normalize score to -1000 to 1000 range
        normalized = max(-1000, min(1000, score * 100))
        self.evaluation_bar.setValue(int(normalized))
        self.evaluation_bar.setFormat(f"{score:.2f}")
        
        # Change color based on who's winning
        if score > 0:
            self.evaluation_bar.setStyleSheet("QProgressBar::chunk { background-color: #22c55e; }")
        elif score < 0:
            self.evaluation_bar.setStyleSheet("QProgressBar::chunk { background-color: #ef4444; }")
        else:
            self.evaluation_bar.setStyleSheet("QProgressBar::chunk { background-color: #f59e0b; }")

    def update_candidates(self, candidates: list):
        """Update the list of top candidate moves."""
        self.candidates_list.clear()
        for i, (san, move, prob) in enumerate(candidates[:3]):
            item = QListWidgetItem(f"{i+1}. {san} ({prob:.1%})")
            self.candidates_list.addItem(item)

    def add_explanation(self, explanation: str):
        """Add an AI explanation to the chat."""
        current = self.explanation_text.toPlainText()
        if current:
            current += "\n\n"
        self.explanation_text.setPlainText(current + explanation)

    def clear_analysis(self):
        """Clear all analysis data for a new game."""
        self.last_move_text.setText("No moves yet")
        self.stats_list.clear()
        self.candidates_list.clear()
        self.explanation_text.clear()
        self.evaluation_bar.setValue(0)
        self.status_text.setText("Ready")