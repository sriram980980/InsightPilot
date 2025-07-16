"""
Main window for InsightPilot application
"""

import logging
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMenuBar, QStatusBar, QSplitter,
    QMessageBox, QApplication, QDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon

from config.config_manager import ConfigManager
from .tabs import ConnectionsTab, QueryChatTab, ResultsTab, HistoryTab
from .dialogs import ConnectionDialog


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config_manager: ConfigManager, client_mode: bool = False):
        super().__init__()
        self.config_manager = config_manager
        self.client_mode = client_mode
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle("InsightPilot - AI-Powered Data Explorer")
        self.setGeometry(100, 100, 1000, 600)
        
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Load UI settings
        self.load_ui_settings()
        
        # Load and apply compact stylesheet
        self.load_stylesheet()
        
        self.logger.info(f"Main window initialized (client_mode: {client_mode})")
    
    def setup_ui(self):
        """Set up the main UI components"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        layout.setSpacing(5)  # Reduced spacing
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Create tab widget for main content
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setDocumentMode(True)  # More compact tabs
        splitter.addWidget(self.tab_widget)
        
        # Add actual tab implementations
        self.setup_tabs()
        
        # Set splitter proportions
        splitter.setSizes([150, 850])  # More compact sidebar
    
    def setup_tabs(self):
        """Set up the application tabs"""
        # Connections Tab
        self.connections_tab = ConnectionsTab(self.config_manager, self)
        self.tab_widget.addTab(self.connections_tab, "Connections")
        
        # Query Chat Tab
        self.query_chat_tab = QueryChatTab(self.config_manager, self)
        self.tab_widget.addTab(self.query_chat_tab, "Query Chat")
        
        # Results Tab
        self.results_tab = ResultsTab(self.config_manager, self)
        self.tab_widget.addTab(self.results_tab, "Results")
        
        # History Tab
        self.history_tab = HistoryTab(self.config_manager, self)
        self.tab_widget.addTab(self.history_tab, "History")
    
    def setup_menu(self):
        """Set up the application menu"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Connection", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_connection)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Set up the status bar"""
        self.status_bar = self.statusBar()
        
        mode_text = "Client Mode" if self.client_mode else "Standalone Mode"
        self.status_bar.showMessage(f"Ready - {mode_text}")
    
    def load_ui_settings(self):
        """Load UI settings from configuration"""
        ui_settings = self.config_manager.get_ui_settings()
        
        # Apply theme
        theme = ui_settings.get("theme", "light")
        self.apply_theme(theme)
        
        # Apply font size
        font_size = ui_settings.get("font_size", 12)
        self.apply_font_size(font_size)
    
    def apply_theme(self, theme: str):
        """Apply UI theme"""
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #3c3c3c;
                }
                QTabBar::tab {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    padding: 8px 16px;
                    border: 1px solid #555555;
                }
                QTabBar::tab:selected {
                    background-color: #3c3c3c;
                }
            """)
        else:
            self.setStyleSheet("")  # Default light theme
    
    def apply_font_size(self, font_size: int):
        """Apply font size to application"""
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)
    
    def load_stylesheet(self):
        """Load and apply the compact stylesheet"""
        try:
            style_path = Path(__file__).parent / "style.qss"
            if style_path.exists():
                with open(style_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                self.logger.info("Compact stylesheet loaded successfully")
        except Exception as e:
            self.logger.warning(f"Failed to load stylesheet: {e}")
    
    def new_connection(self):
        """Handle new connection action"""
        dialog = ConnectionDialog(self.config_manager, parent=self)
        if dialog.exec() == QDialog.Accepted:
            # Refresh the connections tab
            if hasattr(self, 'connections_tab'):
                self.connections_tab.refresh_connections()
            
            QMessageBox.information(
                self,
                "Connection Saved",
                "Database connection has been saved successfully."
            )
    
    def show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(
            self, 
            "Settings", 
            "Settings dialog would open here.\n\nThis will be implemented in the full version."
        )
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, 
            "About InsightPilot", 
            """
            <h3>InsightPilot v1.0.0</h3>
            <p>AI-powered desktop application for data exploration and analysis</p>
            <p>Built with PySide6, Python, and Ollama</p>
            <p><b>Features:</b></p>
            <ul>
                <li>Natural language to SQL conversion</li>
                <li>Multiple database support (MySQL, Oracle, MongoDB)</li>
                <li>Intelligent data visualization</li>
                <li>Secure configuration management</li>
            </ul>
            """
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.logger.info("Application closing")
        event.accept()
