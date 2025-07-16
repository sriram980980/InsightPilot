"""
Results Tab - Query results and visualizations
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QLabel, QSplitter, QComboBox
)
from PySide6.QtCore import Qt


class ResultsTab(QWidget):
    """Tab for displaying query results and visualizations"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the results tab UI"""
        layout = QVBoxLayout(self)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Query Results")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Visualization type selector
        viz_label = QLabel("Visualization:")
        self.viz_combo = QComboBox()
        self.viz_combo.addItems(["Table", "Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot"])
        
        header_layout.addWidget(viz_label)
        header_layout.addWidget(self.viz_combo)
        
        # Export button
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_results)
        header_layout.addWidget(self.export_btn)

        # Edit button (opens dialog)
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        header_layout.addWidget(self.edit_btn)
        
        layout.addLayout(header_layout)
        
        # Create splitter for table and chart
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Results table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        table_label = QLabel("Data Table")
        table_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        table_layout.addWidget(table_label)
        
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.results_table)
        
        splitter.addWidget(table_widget)
        
        # Chart area (placeholder)
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        chart_label = QLabel("Visualization")
        chart_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        chart_layout.addWidget(chart_label)
        
        self.chart_placeholder = QLabel("Chart visualization will appear here")
        self.chart_placeholder.setAlignment(Qt.AlignCenter)
        self.chart_placeholder.setStyleSheet("""
            QLabel {
                background-color: #f8f8f8;
                border: 2px dashed #cccccc;
                border-radius: 10px;
                padding: 20px;
                color: #666666;
            }
        """)
        chart_layout.addWidget(self.chart_placeholder)
        
        splitter.addWidget(chart_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 400])
        
        # Add sample data
        self.load_sample_data()

        # Table is always non-editable
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
    
    def open_edit_dialog(self):
        """Open a dialog to edit the selected row"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidgetItem
        selected = self.results_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Please select a row to edit.")
            return
        # Get current row data
        row_data = [self.results_table.item(selected, col).text() if self.results_table.item(selected, col) else "" for col in range(self.results_table.columnCount())]
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Row")
        layout = QVBoxLayout(dialog)
        edits = []
        for i, header in enumerate([self.results_table.horizontalHeaderItem(j).text() for j in range(self.results_table.columnCount())]):
            hlayout = QHBoxLayout()
            hlayout.addWidget(QLabel(header))
            edit = QLineEdit(row_data[i])
            edits.append(edit)
            hlayout.addWidget(edit)
            layout.addLayout(hlayout)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        def save():
            for col, edit in enumerate(edits):
                self.results_table.setItem(selected, col, QTableWidgetItem(edit.text()))
            dialog.accept()
        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()
    def load_sample_data(self):
        """Load sample data for demonstration"""
        # Sample data
        headers = ["Order ID", "Customer", "Product", "Quantity", "Revenue"]
        data = [
            ["1001", "John Doe", "Widget A", "5", "$250.00"],
            ["1002", "Jane Smith", "Widget B", "3", "$150.00"],
            ["1003", "Bob Johnson", "Widget A", "7", "$350.00"],
            ["1004", "Alice Brown", "Widget C", "2", "$100.00"],
        ]
        
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        self.results_table.setRowCount(len(data))
        
        for row, row_data in enumerate(data):
            for col, cell_data in enumerate(row_data):
                from PySide6.QtWidgets import QTableWidgetItem
                self.results_table.setItem(row, col, QTableWidgetItem(cell_data))
        
        # Auto-resize columns
        self.results_table.resizeColumnsToContents()

        # Prevent editing by double-click or keypress
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
    
    def export_results(self):
        """Export results to file"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Export Results",
            "Export functionality will be implemented in the full version.\n\nSupported formats: CSV, Excel, PNG (charts)"
        )
