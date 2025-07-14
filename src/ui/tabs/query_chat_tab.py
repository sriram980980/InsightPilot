"""
Query Chat Tab - Natural language query interface
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QSplitter
)
from PySide6.QtCore import Qt


class QueryChatTab(QWidget):
    """Tab for natural language query interface"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the query chat tab UI"""
        layout = QVBoxLayout(self)
        
        # Create splitter for chat history and input
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Chat history area
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        
        history_label = QLabel("Query History & Responses")
        history_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        history_layout.addWidget(history_label)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("Query history and AI responses will appear here...")
        history_layout.addWidget(self.chat_history)
        
        splitter.addWidget(history_widget)
        
        # Query input area
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        input_label = QLabel("Ask a question about your data:")
        input_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        input_layout.addWidget(input_label)
        
        self.query_input = QTextEdit()
        self.query_input.setMaximumHeight(100)
        self.query_input.setPlaceholderText("e.g., 'Show me all orders from last week' or 'Which customers have the highest revenue?'")
        input_layout.addWidget(self.query_input)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.clear_btn = QPushButton("Clear")
        self.send_btn = QPushButton("Send Query")
        self.send_btn.setDefault(True)
        
        self.clear_btn.clicked.connect(self.clear_input)
        self.send_btn.clicked.connect(self.send_query)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(button_layout)
        splitter.addWidget(input_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 200])
    
    def clear_input(self):
        """Clear the query input"""
        self.query_input.clear()
    
    def send_query(self):
        """Send the query for processing"""
        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            return
        
        # Add query to history
        self.chat_history.append(f"<b>You:</b> {query_text}")
        self.chat_history.append("<b>AI:</b> [This will be implemented in the full version - natural language to SQL conversion]")
        self.chat_history.append("")
        
        # Clear input
        self.query_input.clear()
        
        self.logger.info(f"Query sent: {query_text}")
