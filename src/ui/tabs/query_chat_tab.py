"""
Query Chat Tab - Natural language query interface with LLM integration
"""

import logging
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QSplitter, QComboBox, QGroupBox,
    QFormLayout, QMessageBox, QProgressBar, QTextBrowser
)
from PySide6.QtCore import Qt, QThread, Signal

from api.client_api import ClientAPI, QueryRequest, QueryResponse


class QueryExecutionThread(QThread):
    """Thread for executing queries in background"""
    
    query_completed = Signal(object)  # QueryResponse
    progress_updated = Signal(str)
    
    def __init__(self, client_api: ClientAPI, query_request: QueryRequest):
        super().__init__()
        self.client_api = client_api
        self.query_request = query_request
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Execute the query in background"""
        try:
            self.progress_updated.emit("Getting database schema...")
            schema = self.client_api.get_schema(
                self.query_request.database_name,
                self.query_request.database_type
            )
            
            self.progress_updated.emit("Generating SQL query with LLM...")
            response = self.client_api.execute_query(self.query_request)
            
            self.query_completed.emit(response)
            
        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            error_response = QueryResponse(
                success=False,
                sql_query="",
                result=None,
                explanation="",
                error=str(e)
            )
            self.query_completed.emit(error_response)


class QueryChatTab(QWidget):
    """Tab for natural language query interface with LLM integration"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize client API for backend communication
        self.client_api = ClientAPI(config_manager)
        self.query_thread = None
        
        self.setup_ui()
        self.load_connections()
    
    def setup_ui(self):
        """Set up the query chat tab UI"""
        layout = QVBoxLayout(self)
        
        # Configuration section
        config_group = QGroupBox("Query Configuration")
        config_layout = QFormLayout(config_group)
        
        # Database connection dropdown
        self.db_connection_combo = QComboBox()
        self.db_connection_combo.setPlaceholderText("Select database connection...")
        config_layout.addRow("Database Connection:", self.db_connection_combo)
        
        # LLM connection dropdown
        self.llm_connection_combo = QComboBox()
        self.llm_connection_combo.setPlaceholderText("Select LLM connection...")
        config_layout.addRow("LLM Connection:", self.llm_connection_combo)
        
        # Visualization framework dropdown
        self.viz_framework_combo = QComboBox()
        self.viz_framework_combo.addItems([
            "Auto-detect",
            "Table View",
            "Bar Chart", 
            "Line Chart",
            "Pie Chart",
            "Scatter Plot"
        ])
        self.viz_framework_combo.setCurrentText("Auto-detect")
        config_layout.addRow("Visualization:", self.viz_framework_combo)
        
        # Refresh connections button
        refresh_btn = QPushButton("🔄 Refresh Connections")
        refresh_btn.clicked.connect(self.load_connections)
        config_layout.addRow("", refresh_btn)
        
        layout.addWidget(config_group)
        
        # Create splitter for chat history and input
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # Chat history area
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        
        history_label = QLabel("Query History & AI Responses")
        history_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        history_layout.addWidget(history_label)
        
        self.chat_history = QTextBrowser()
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
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        input_layout.addWidget(self.progress_bar)
        
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
        splitter.setSizes([400, 250])
        
    def load_connections(self):
        """Load available database and LLM connections"""
        try:
            connections = self.config_manager.get_connections()
            
            # Clear existing items
            self.db_connection_combo.clear()
            self.llm_connection_combo.clear()
            
            # Populate database connections
            db_connections = [conn for conn in connections if conn.get('type') != 'LLM']
            for conn in db_connections:
                self.db_connection_combo.addItem(
                    f"{conn['name']} ({conn.get('database_type', 'Unknown')})",
                    conn['name']
                )
            
            # Populate LLM connections  
            llm_connections = [conn for conn in connections if conn.get('type') == 'LLM']
            for conn in llm_connections:
                self.llm_connection_combo.addItem(
                    f"{conn['name']} ({conn.get('provider', 'Unknown')})",
                    conn['name']
                )
            
            self.logger.info(f"Loaded {len(db_connections)} database and {len(llm_connections)} LLM connections")
            
        except Exception as e:
            self.logger.error(f"Error loading connections: {e}")
            QMessageBox.warning(
                self,
                "Connection Error",
                f"Failed to load connections: {str(e)}"
            )
    
    def clear_input(self):
        """Clear the query input"""
        self.query_input.clear()
    
    def send_query(self):
        """Send the query for processing"""
        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            QMessageBox.warning(self, "Input Required", "Please enter a query.")
            return
        
        # Validate selections
        if self.db_connection_combo.currentData() is None:
            QMessageBox.warning(self, "Selection Required", "Please select a database connection.")
            return
            
        if self.llm_connection_combo.currentData() is None:
            QMessageBox.warning(self, "Selection Required", "Please select an LLM connection.")
            return
        
        # Disable UI during processing
        self.send_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Add query to history
        self.add_to_history(f"<b>You:</b> {query_text}", "user")
        
        # Get selected connection info
        db_connection = self.db_connection_combo.currentData()
        llm_connection = self.llm_connection_combo.currentData()
        viz_type = self.viz_framework_combo.currentText()
        
        # Get database type from connection config
        connections = self.config_manager.get_connections()
        db_config = next((c for c in connections if c['name'] == db_connection), {})
        database_type = db_config.get('database_type', 'mysql')
        
        # Create query request
        query_request = QueryRequest(
            database_name=db_connection,
            question=query_text,
            database_type=database_type
        )
        
        # Start query execution in background thread
        self.query_thread = QueryExecutionThread(self.client_api, query_request)
        self.query_thread.query_completed.connect(self.on_query_completed)
        self.query_thread.progress_updated.connect(self.on_progress_updated)
        self.query_thread.start()
        
        # Clear input
        self.query_input.clear()
        
        self.logger.info(f"Query sent: {query_text} (DB: {db_connection}, LLM: {llm_connection})")
    
    def on_progress_updated(self, message: str):
        """Handle progress updates"""
        self.add_to_history(f"<i>{message}</i>", "system")
    
    def on_query_completed(self, response: QueryResponse):
        """Handle completed query"""
        # Re-enable UI
        self.send_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if response.success:
            # Display AI response with generated SQL
            ai_response = f"""<b>AI:</b> {response.explanation}
            
<b>Generated SQL:</b>
<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; font-family: monospace;">
{response.sql_query}
</pre>"""
            
            if response.result:
                ai_response += f"""
<b>Results:</b> {response.result.total_rows} rows returned in {response.execution_time:.2f}s
<i>Data visualization will be implemented in the next phase.</i>"""
            
            self.add_to_history(ai_response, "assistant")
            
        else:
            error_msg = f"<b>AI:</b> <span style='color: red;'>Error: {response.error}</span>"
            self.add_to_history(error_msg, "error")
        
        # Clean up thread
        if self.query_thread:
            self.query_thread.deleteLater()
            self.query_thread = None
    
    def add_to_history(self, message: str, sender_type: str):
        """Add message to chat history with styling"""
        if sender_type == "user":
            styled_message = f"<div style='margin: 10px 0; padding: 10px; background-color: #e3f2fd; border-radius: 5px;'>{message}</div>"
        elif sender_type == "assistant":
            styled_message = f"<div style='margin: 10px 0; padding: 10px; background-color: #f3e5f5; border-radius: 5px;'>{message}</div>"
        elif sender_type == "system":
            styled_message = f"<div style='margin: 5px 0; padding: 5px; color: #666; font-style: italic;'>{message}</div>"
        else:  # error
            styled_message = f"<div style='margin: 10px 0; padding: 10px; background-color: #ffebee; border-radius: 5px;'>{message}</div>"
        
        self.chat_history.append(styled_message)
        
        # Scroll to bottom
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
