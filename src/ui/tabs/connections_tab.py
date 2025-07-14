"""
Connections Tab - Database connection management
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QMessageBox
)
from PySide6.QtCore import Qt

# Import the connection test thread from the dialog
from ..dialogs.connection_dialog import ConnectionTestThread, ConnectionDialog


class ConnectionsTab(QWidget):
    """Tab for managing database connections"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.test_thread = None
        
        self.setup_ui()
        self.load_connections()
    
    def setup_ui(self):
        """Set up the connections tab UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Database Connections")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Buttons
        self.new_btn = QPushButton("New Connection")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.test_btn = QPushButton("Test Connection")
        
        self.new_btn.clicked.connect(self.new_connection)
        self.edit_btn.clicked.connect(self.edit_connection)
        self.delete_btn.clicked.connect(self.delete_connection)
        self.test_btn.clicked.connect(self.test_connection)
        
        header_layout.addWidget(self.new_btn)
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.delete_btn)
        header_layout.addWidget(self.test_btn)
        
        layout.addLayout(header_layout)
        
        # Connections table
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(5)
        self.connections_table.setHorizontalHeaderLabels([
            "Name", "Type", "Host", "Database", "Status"
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
        
        layout.addWidget(self.connections_table)
        
        # Initially disable edit/delete/test buttons
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
    
    def load_connections(self):
        """Load connections from config manager"""
        try:
            connections = self.config_manager.get_connections()
            self.connections_table.setRowCount(len(connections))
            
            for row, (name, config) in enumerate(connections.items()):
                self.connections_table.setItem(row, 0, QTableWidgetItem(name))
                self.connections_table.setItem(row, 1, QTableWidgetItem(config.get('type', 'Unknown')))
                self.connections_table.setItem(row, 2, QTableWidgetItem(config.get('host', '')))
                self.connections_table.setItem(row, 3, QTableWidgetItem(config.get('database', '')))
                self.connections_table.setItem(row, 4, QTableWidgetItem('Not Tested'))
                
        except Exception as e:
            self.logger.error(f"Error loading connections: {e}")
    
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
            
            # Open connection dialog for editing
            dialog = ConnectionDialog(self.config_manager, connection_name, parent=self)
            if dialog.exec() == dialog.Accepted:
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
                
                # Disable test button during test
                self.test_btn.setEnabled(False)
                self.test_btn.setText("Testing...")
                
                # Update status in table
                self.connections_table.setItem(current_row, 4, QTableWidgetItem("Testing..."))
                
                # Start connection test in separate thread
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
