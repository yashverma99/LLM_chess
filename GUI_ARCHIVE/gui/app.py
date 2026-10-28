"""Main application entry point for the Chess AI Hybrid GUI."""
import sys
import os
# Add the project root directory to Python's path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    
    # Set application-wide attributes
    app.setApplicationName("Chess AI Hybrid")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Chess AI Project")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()