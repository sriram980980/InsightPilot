"""
History Tab - Query history and favorites
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QMessageBox, QSplitter, QTextEdit
)
from PySide6.QtCore import Qt


class HistoryTab(QWidget):
    """Tab for managing query history and favorites"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.load_history()
    
    def setup_ui(self):
        """Set up the history tab UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Query History & Favorites")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Buttons
        self.favorite_btn = QPushButton("Add to Favorites")
        self.rerun_btn = QPushButton("Re-run Query")
        self.delete_btn = QPushButton("Delete")
        self.clear_all_btn = QPushButton("Clear All")
        
        self.favorite_btn.clicked.connect(self.add_to_favorites)
        self.rerun_btn.clicked.connect(self.rerun_query)
        self.delete_btn.clicked.connect(self.delete_history_item)
        self.clear_all_btn.clicked.connect(self.clear_all_history)
        
        header_layout.addWidget(self.favorite_btn)
        header_layout.addWidget(self.rerun_btn)
        header_layout.addWidget(self.delete_btn)
        header_layout.addWidget(self.clear_all_btn)
        
        layout.addLayout(header_layout)
        
        # Create splitter for history table and query preview
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        # History table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        table_label = QLabel("Query History")
        table_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        table_layout.addWidget(table_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Timestamp", "Natural Language Query", "Database", "Status", "Favorite"
        ])
        
        # Set column widths
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        table_layout.addWidget(self.history_table)
        splitter.addWidget(table_widget)
        
        # Query preview area
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        preview_label = QLabel("Generated SQL Query")
        preview_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        preview_layout.addWidget(preview_label)
        
        self.query_preview = QTextEdit()
        self.query_preview.setReadOnly(True)
        self.query_preview.setMaximumHeight(150)
        self.query_preview.setPlaceholderText("Select a query from the history to view the generated SQL!")
        preview_layout.addWidget(self.query_preview)
        
        splitter.addWidget(preview_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 150])
        
        # Initially disable buttons
        self.favorite_btn.setEnabled(False)
        self.rerun_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
    
    def load_history(self):
        """Load query history"""
        # Sample history data
        history_data = [
            ["2025-07-13 10:30:15", "Show me all orders from last week", "MySQL_Sales", "Success", "★"],
            ["2025-07-13 09:45:22", "Which customers have the highest revenue?", "MySQL_Sales", "Success", ""],
            ["2025-07-12 16:20:10", "List all products with low inventory", "Oracle_Inventory", "Success", "★"],
            ["2025-07-12 14:15:33", "Show monthly sales trends", "MySQL_Sales", "Error", ""],
        ]
        
        self.history_table.setRowCount(len(history_data))
        
        for row, row_data in enumerate(history_data):
            for col, cell_data in enumerate(row_data):
                self.history_table.setItem(row, col, QTableWidgetItem(cell_data))
    
    def on_selection_changed(self):
        """Handle selection change in history table"""
        has_selection = len(self.history_table.selectedItems()) > 0
        self.favorite_btn.setEnabled(has_selection)
        self.rerun_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        # Show SQL query preview for selected item
        if has_selection:
            current_row = self.history_table.currentRow()
            query_text = self.history_table.item(current_row, 1).text()
            
            # Sample SQL based on the natural language query
            sample_sql = f"-- Generated SQL for: {query_text}\nSELECT * FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 WEEK);"
            self.query_preview.setPlainText(sample_sql)
        else:
            self.query_preview.clear()
    
    def add_to_favorites(self):
        """Add selected query to favorites"""
        current_row = self.history_table.currentRow()
        if current_row >= 0:
            # Toggle favorite status
            current_favorite = self.history_table.item(current_row, 4).text()
            new_favorite = "★" if current_favorite == "" else ""
            self.history_table.setItem(current_row, 4, QTableWidgetItem(new_favorite))
    
    def rerun_query(self):
        """Re-run the selected query"""
        current_row = self.history_table.currentRow()
        if current_row >= 0:
            query_text = self.history_table.item(current_row, 1).text()
            QMessageBox.information(
                self,
                "Re-run Query",
                f"Re-running query: '{query_text}'\n\nThis will be implemented in the full version."
            )
    
    def delete_history_item(self):
        """Delete selected history item"""
        current_row = self.history_table.currentRow()
        if current_row >= 0:
            query_text = self.history_table.item(current_row, 1).text()
            reply = QMessageBox.question(
                self,
                "Delete History Item",
                f"Are you sure you want to delete this query from history?\n\n'{query_text}'",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.history_table.removeRow(current_row)
    
    def clear_all_history(self):
        """Clear all history"""
        reply = QMessageBox.question(
            self,
            "Clear All History",
            "Are you sure you want to clear all query history?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.history_table.setRowCount(0)
