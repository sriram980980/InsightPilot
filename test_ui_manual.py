"""
Test the new connection dialog and tab functionality
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication
from config.config_manager import ConfigManager
from ui.main_window import MainWindow


def test_ui():
    """Test the UI components"""
    app = QApplication(sys.argv)
    
    # Create config manager
    config_manager = ConfigManager()
    
    # Create main window
    window = MainWindow(config_manager, client_mode=False)
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    test_ui()
