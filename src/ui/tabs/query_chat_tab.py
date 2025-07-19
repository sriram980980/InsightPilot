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
from llm.llm_client import LLMClient
from ui.widgets.result_viewer import ResultViewer


class QueryExecutionThread(QThread):
    """Thread for executing queries in background"""
    
    query_completed = Signal(object)  # QueryResponse
    progress_updated = Signal(str)
    table_scanned = Signal(str)  # Individual table scanned
    
    def __init__(self, client_api: ClientAPI, query_request: QueryRequest):
        super().__init__()
        self.client_api = client_api
        self.query_request = query_request
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Execute the query in background"""
        try:
            self.progress_updated.emit("🔍 Connecting to database!")
            
            # Enhanced execute_query call with progress callback
            response = self.client_api.execute_query_with_progress(
                self.query_request, 
                progress_callback=self.progress_updated.emit,
                table_callback=self.table_scanned.emit
            )
            
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
        self.parent_window = parent  # Store reference to main window
        self.logger = logging.getLogger(__name__)
        
        # Initialize client API for backend communication
        self.client_api = ClientAPI(config_manager)
        self.query_thread = None
        
        # Initialize LLM client for result viewer
        try:
            self.llm_client = self.client_api._init_llm_client()
        except Exception as e:
            self.logger.warning(f"Failed to initialize LLM client: {e}")
            self.llm_client = None
        
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
        self.db_connection_combo.setPlaceholderText("Select database connection!")
        config_layout.addRow("Database Connection:", self.db_connection_combo)
        
        # LLM connection dropdown
        self.llm_connection_combo = QComboBox()
        self.llm_connection_combo.setPlaceholderText("Select LLM connection!")
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
        self.chat_history.setPlaceholderText("Query history and AI responses will appear here!")
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
            connections_dict = self.config_manager.get_connections()
            # Convert to list of dicts, adding 'name' key
            connections = []
            for name, conn in connections_dict.items():
                if isinstance(conn, dict):
                    conn = dict(conn)  # copy
                    conn['name'] = name
                    connections.append(conn)
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
            
            # Add LLM providers to the combo as well
            llm_providers = self.config_manager.get_llm_providers()
            for provider_name, provider_config in llm_providers.items():
                if provider_config.get("enabled", True):
                    self.llm_connection_combo.addItem(
                        f"{provider_name} ({provider_config.get('provider', 'Unknown')})",
                        provider_name
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
        db_config = {}
        if isinstance(connections, dict):
            # If connections is a dict of connection dicts
            db_config = connections.get(db_connection, {})
        elif isinstance(connections, list):
            # If connections is a list of dicts
            db_config = next((c for c in connections if c.get('name') == db_connection), {})
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
        self.query_thread.table_scanned.connect(self.on_table_scanned)
        self.query_thread.start()
        
        # Clear input
        self.query_input.clear()
        
        self.logger.info(f"Query sent: {query_text} (DB: {db_connection}, LLM: {llm_connection})")
    
    def on_progress_updated(self, message: str):
        """Handle progress updates"""
        self.add_to_history(f"<i>🔄 {message}</i>", "system")
    
    def on_table_scanned(self, table_name: str):
        """Handle table scan updates"""
        self.add_to_history(f"<i>📋 Found table: <strong>{table_name}</strong></i>", "system")
    
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
<b>Results:</b> {response.result.row_count} rows returned in {response.execution_time:.2f}s
<i>Results have been sent to the Results tab for visualization.</i>"""
                
                # Push results to Results tab
                self.push_results_to_tab(response.result, response.sql_query, response.explanation)
            
            self.add_to_history(ai_response, "assistant")
            
        else:
            error_msg = f"<b>AI:</b> <span style='color: red;'>Error: {response.error}</span>"
            self.add_to_history(error_msg, "error")
        
        # Clean up thread
        if self.query_thread:
            self.query_thread.deleteLater()
            self.query_thread = None
    
    def push_results_to_tab(self, result, sql_query: str, explanation: str):
        """Push query results to the Results tab"""
        try:
            # Get reference to main window and results tab
            if self.parent_window and hasattr(self.parent_window, 'results_tab'):
                # Switch to Results tab
                tab_widget = self.parent_window.tab_widget
                results_tab_index = tab_widget.indexOf(self.parent_window.results_tab)
                if results_tab_index != -1:
                    tab_widget.setCurrentIndex(results_tab_index)
                
                # Load results into the Results tab
                self.parent_window.results_tab.load_query_results(result, sql_query, explanation)
                
                self.logger.info("Results pushed to Results tab successfully")
            else:
                self.logger.warning("Cannot access Results tab - parent window reference not available")
        except Exception as e:
            self.logger.error(f"Error pushing results to Results tab: {e}")
    
    def add_to_history(self, message: str, sender_type: str):
        """Add message to chat history with styling"""
        if sender_type == "user":
            styled_message = f"<div style='margin: 10px 0; padding: 10px; background-color: #e3f2fd; border-radius: 5px;'>{message}</div>"
        elif sender_type == "assistant":
            styled_message = f"<div style='margin: 10px 0; padding: 10px; background-color: #f3e5f5; border-radius: 5px;'>{message}</div>"
        elif sender_type == "system":
            styled_message = f"<div style='margin: 5px 0; padding: 8px; color: #555; font-style: italic; background-color: #f8f9fa; border-left: 3px solid #007bff; border-radius: 3px;'>{message}</div>"
        else:  # error
            styled_message = f"<div style='margin: 10px 0; padding: 10px; background-color: #ffebee; border-radius: 5px;'>{message}</div>"
        
        self.chat_history.append(styled_message)
        
        # Scroll to bottom
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def refresh_llm_client(self):
        """Refresh the LLM client configuration"""
        try:
            # Reinitialize client API which will create new enhanced LLM client
            self.client_api = ClientAPI(self.config_manager)
            
            # Update LLM client reference
            try:
                self.llm_client = self.client_api._init_llm_client()
            except Exception as e:
                self.logger.warning(f"Failed to refresh LLM client: {e}")
                self.llm_client = None
            
            # Reload connections to reflect provider changes
            self.load_connections()
            
            self.logger.info("LLM client refreshed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh LLM client: {e}")
