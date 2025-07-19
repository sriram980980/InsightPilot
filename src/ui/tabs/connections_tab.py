"""
Connections Tab - Database and LLM connection management
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QMessageBox, QComboBox, QGroupBox, QProgressBar, QDialog
)
from PySide6.QtCore import Qt

# Import the connection test thread from the dialog
from ..dialogs.connection_dialog import ConnectionTestThread, ConnectionDialog
from ..dialogs.llm_connection_dialog import LLMConnectionDialog
from llm.llm_service import LLMService


class ConnectionsTab(QWidget):
    """Tab for managing database and LLM connections"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.test_thread = None
        self.llm_service = LLMService()
        self.llm_startup_thread = None
        
        self.setup_ui()
        self.load_connections()
    
    def setup_ui(self):
        """Set up the connections tab UI"""
        layout = QVBoxLayout(self)
        
        # LLM Control Section
        llm_group = QGroupBox("LLM Model Control")
        llm_layout = QVBoxLayout(llm_group)
        
        # LLM status and controls
        llm_control_layout = QHBoxLayout()
        
        self.llm_status_label = QLabel("LLM Status: Checking!")
        self.llm_status_label.setStyleSheet("font-weight: bold;")
        llm_control_layout.addWidget(self.llm_status_label)
        
        llm_control_layout.addStretch()
        
        self.start_llm_btn = QPushButton("Start Local LLM")
        self.start_llm_btn.clicked.connect(self.start_local_llm)
        llm_control_layout.addWidget(self.start_llm_btn)
        
        self.stop_llm_btn = QPushButton("Stop LLM")
        self.stop_llm_btn.clicked.connect(self.stop_local_llm)
        self.stop_llm_btn.setEnabled(False)
        llm_control_layout.addWidget(self.stop_llm_btn)
        
        llm_layout.addLayout(llm_control_layout)
        
        # LLM progress bar
        self.llm_progress = QProgressBar()
        self.llm_progress.setVisible(False)
        llm_layout.addWidget(self.llm_progress)
        
        # LLM progress message
        self.llm_progress_label = QLabel("")
        self.llm_progress_label.setVisible(False)
        self.llm_progress_label.setStyleSheet("color: blue; font-size: 11px;")
        llm_layout.addWidget(self.llm_progress_label)
        
        layout.addWidget(llm_group)
        
        # Connections Section
        connections_group = QGroupBox("Database & LLM Connections")
        connections_layout = QVBoxLayout(connections_group)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Connections")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Connection type filter
        self.connection_filter = QComboBox()
        self.connection_filter.addItems(["All", "Database", "LLM"])
        self.connection_filter.currentTextChanged.connect(self.filter_connections)
        header_layout.addWidget(QLabel("Filter:"))
        header_layout.addWidget(self.connection_filter)
        
        connections_layout.addLayout(header_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_db_btn = QPushButton("New Database")
        self.new_llm_btn = QPushButton("New LLM")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.test_btn = QPushButton("Test Connection")
        
        self.new_db_btn.clicked.connect(self.new_db_connection)
        self.new_llm_btn.clicked.connect(self.new_llm_connection)
        self.edit_btn.clicked.connect(self.edit_connection)
        self.delete_btn.clicked.connect(self.delete_connection)
        self.test_btn.clicked.connect(self.test_connection)
        
        button_layout.addWidget(self.new_db_btn)
        button_layout.addWidget(self.new_llm_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.test_btn)
        button_layout.addStretch()
        
        connections_layout.addLayout(button_layout)
        
        # Connections table
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(5)
        self.connections_table.setHorizontalHeaderLabels([
            "Name", "Type", "Host", "Database/Model", "Status"
        ])
        
        # Set column widths
        header = self.connections_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.connections_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.connections_table.setAlternatingRowColors(True)
        self.connections_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        connections_layout.addWidget(self.connections_table)
        self.connections_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(connections_group)

        # Initially disable edit/delete/test buttons
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
        
        # Check initial LLM status
        self.check_llm_status()
    
    def load_connections(self):
        """Load connections from config manager"""
        try:
            connections = self.config_manager.get_connections()
            self.all_connections = connections
            self.filter_connections()
                
        except Exception as e:
            self.logger.error(f"Error loading connections: {e}")
    
    def filter_connections(self):
        """Filter connections based on selected type"""
        filter_type = self.connection_filter.currentText()
        
        if not hasattr(self, 'all_connections'):
            self.all_connections = self.config_manager.get_connections()
        
        if filter_type == "All":
            filtered_connections = self.all_connections
        elif filter_type == "Database":
            filtered_connections = {name: config for name, config in self.all_connections.items() 
                                  if config.get('type') in ['MySQL', 'Oracle', 'MongoDB']}
        elif filter_type == "LLM":
            filtered_connections = {name: config for name, config in self.all_connections.items() 
                                  if config.get('type') == 'LLM'}
        else:
            filtered_connections = self.all_connections
        
        self.connections_table.setRowCount(len(filtered_connections))
        
        for row, (name, config) in enumerate(filtered_connections.items()):
            self.connections_table.setItem(row, 0, QTableWidgetItem(name))
            self.connections_table.setItem(row, 1, QTableWidgetItem(config.get('type', 'Unknown')))
            self.connections_table.setItem(row, 2, QTableWidgetItem(config.get('host', '')))
            
            # Handle different connection types for the database/model column
            if config.get('type') == 'LLM':
                self.connections_table.setItem(row, 3, QTableWidgetItem(config.get('model', '')))
            else:
                self.connections_table.setItem(row, 3, QTableWidgetItem(config.get('database', '')))
            
            self.connections_table.setItem(row, 4, QTableWidgetItem('Not Tested'))
    
    def on_selection_changed(self):
        """Handle selection change in connections table"""
        has_selection = len(self.connections_table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.test_btn.setEnabled(has_selection)
    
    def new_connection(self):
        """Handle new connection button click"""
        # This will be handled by the main window
        if hasattr(self.parent(), 'new_connection'):
            self.parent().new_connection()
    
    def edit_connection(self):
        """Handle edit connection button click"""
        current_row = self.connections_table.currentRow()
        if current_row >= 0:
            connection_name = self.connections_table.item(current_row, 0).text()
            connection_type = self.connections_table.item(current_row, 1).text()
            
            # Open appropriate dialog based on connection type
            if connection_type == 'LLM':
                dialog = LLMConnectionDialog(self.config_manager, connection_name, parent=self)
            else:
                dialog = ConnectionDialog(self.config_manager, connection_name, parent=self)
                
            if dialog.exec() == QDialog.Accepted:
                # Refresh the connections table
                self.load_connections()
                QMessageBox.information(
                    self,
                    "Connection Updated",
                    f"Connection '{connection_name}' has been updated successfully."
                )
    
    def delete_connection(self):
        """Handle delete connection button click"""
        current_row = self.connections_table.currentRow()
        if current_row >= 0:
            connection_name = self.connections_table.item(current_row, 0).text()
            reply = QMessageBox.question(
                self,
                "Delete Connection",
                f"Are you sure you want to delete the connection '{connection_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Remove from config and refresh table
                self.config_manager.remove_connection(connection_name)
                self.load_connections()
    
    def test_connection(self):
        """Handle test connection button click"""
        current_row = self.connections_table.currentRow()
        if current_row >= 0:
            connection_name = self.connections_table.item(current_row, 0).text()
            
            # Get connection config
            connections = self.config_manager.get_connections()
            if connection_name in connections:
                config = connections[connection_name]
                connection_type = config.get('type', 'Unknown')
                
                # Disable test button during test
                self.test_btn.setEnabled(False)
                self.test_btn.setText("Testing!")
                
                # Update status in table
                self.connections_table.setItem(current_row, 4, QTableWidgetItem("Testing!"))
                
                # Start appropriate connection test
                if connection_type == 'LLM':
                    # Import here to avoid circular imports
                    from ..dialogs.llm_connection_dialog import LLMTestThread
                    self.test_thread = LLMTestThread(config)
                else:
                    self.test_thread = ConnectionTestThread(config)
                
                self.test_thread.result_ready.connect(
                    lambda success, message: self.on_test_result(current_row, success, message)
                )
                self.test_thread.start()
            else:
                QMessageBox.warning(
                    self,
                    "Connection Not Found",
                    f"Connection '{connection_name}' not found in configuration."
                )
    
    def on_test_result(self, row, success, message):
        """Handle connection test result"""
        # Re-enable test button
        self.test_btn.setEnabled(True)
        self.test_btn.setText("Test Connection")
        
        # Update status in table
        status = "Connected" if success else "Failed"
        self.connections_table.setItem(row, 4, QTableWidgetItem(status))
        
        # Show result message
        if success:
            QMessageBox.information(self, "Connection Test", message)
        else:
            QMessageBox.warning(self, "Connection Test Failed", message)
    
    def refresh_connections(self):
        """Refresh the connections table"""
        self.load_connections()
    
    # LLM Control Methods
    def check_llm_status(self):
        """Check current LLM status"""
        status = self.llm_service.get_status()
        if status["running"]:
            self.llm_status_label.setText(f"LLM Status: Running ({len(status['models'])} models)")
            self.llm_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.start_llm_btn.setEnabled(False)
            self.stop_llm_btn.setEnabled(True)
        else:
            # Check if Ollama is installed
            installed, version = self.llm_service.check_ollama_installation()
            if installed:
                self.llm_status_label.setText(f"LLM Status: Stopped ({version})")
                self.llm_status_label.setStyleSheet("color: orange; font-weight: bold;")
                self.start_llm_btn.setEnabled(True)
                self.stop_llm_btn.setEnabled(False)
            else:
                self.llm_status_label.setText("LLM Status: Ollama not installed")
                self.llm_status_label.setStyleSheet("color: red; font-weight: bold;")
                self.start_llm_btn.setEnabled(False)
                self.stop_llm_btn.setEnabled(False)
    
    def start_local_llm(self):
        """Start the local LLM model"""
        if self.llm_startup_thread and self.llm_startup_thread.isRunning():
            return
        
        self.llm_startup_thread = self.llm_service.start_model()
        if self.llm_startup_thread:
            # Connect signals
            self.llm_startup_thread.startup_progress.connect(self.on_llm_progress)
            self.llm_startup_thread.startup_complete.connect(self.on_llm_startup_complete)
            self.llm_startup_thread.model_pulled.connect(self.on_model_pulled)
            
            # Update UI
            self.start_llm_btn.setEnabled(False)
            self.llm_progress.setVisible(True)
            self.llm_progress.setRange(0, 0)  # Indeterminate
            self.llm_progress_label.setVisible(True)
            self.llm_progress_label.setText("Initializing LLM startup!")
            
            # Start the thread
            self.llm_startup_thread.start()
    
    def stop_local_llm(self):
        """Stop the local LLM model"""
        self.llm_service.stop_model()
        self.check_llm_status()
    
    def on_llm_progress(self, message):
        """Handle LLM startup progress"""
        self.llm_progress_label.setText(message)
    
    def on_llm_startup_complete(self, success, message):
        """Handle LLM startup completion"""
        self.llm_progress.setVisible(False)
        self.llm_progress_label.setVisible(False)
        
        if success:
            QMessageBox.information(self, "LLM Started", message)
            self.check_llm_status()
        else:
            QMessageBox.critical(self, "LLM Startup Failed", message)
            self.start_llm_btn.setEnabled(True)
    
    def on_model_pulled(self, model_name):
        """Handle model pull completion"""
        self.llm_progress_label.setText(f"Model {model_name} downloaded successfully")
    
    def new_db_connection(self):
        """Create a new database connection"""
        self.new_connection()
    
    def new_llm_connection(self):
        """Create a new LLM connection"""
        dialog = LLMConnectionDialog(self.config_manager, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_connections()
            QMessageBox.information(
                self,
                "Connection Saved",
                "LLM connection has been saved successfully."
            )
