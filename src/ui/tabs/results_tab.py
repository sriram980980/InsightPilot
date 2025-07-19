"""
Results Tab - Query results and visualizations
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QLabel, QSplitter, QComboBox, QTableWidgetItem,
    QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from adapters.base_adapter import QueryResult
from visualization.chart_renderer import ChartRenderer


class ResultsTab(QWidget):
    """Tab for displaying query results and visualizations"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize chart renderer
        self.chart_renderer = ChartRenderer()
        self.current_result = None
        self.current_sql = ""
        self.current_explanation = ""
        
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
        self.viz_combo.addItems(["Table", "Auto-detect", "Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot", "Histogram"])
        self.viz_combo.currentTextChanged.connect(self.on_visualization_changed)
        
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
        
        # Chart area
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        chart_label = QLabel("Visualization")
        chart_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        chart_layout.addWidget(chart_label)
        
        # Create scroll area for chart
        self.chart_scroll = QScrollArea()
        self.chart_scroll.setWidgetResizable(True)
        self.chart_scroll.setAlignment(Qt.AlignCenter)
        
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
        self.chart_scroll.setWidget(self.chart_placeholder)
        chart_layout.addWidget(self.chart_scroll)
        
        splitter.addWidget(chart_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 400])
        
        # Initially load sample data
        self.load_sample_data()

        # Table is always non-editable
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
    
    def load_query_results(self, result: QueryResult, sql_query: str = "", explanation: str = ""):
        """Load actual query results from QueryChatTab"""
        try:
            self.current_result = result
            self.current_sql = sql_query
            self.current_explanation = explanation
            
            # Clear existing data
            self.results_table.clear()
            
            # Set up table with new data
            if result.columns and result.rows:
                self.results_table.setColumnCount(len(result.columns))
                self.results_table.setHorizontalHeaderLabels(result.columns)
                self.results_table.setRowCount(len(result.rows))
                
                # Populate table
                for row_idx, row_data in enumerate(result.rows):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                        self.results_table.setItem(row_idx, col_idx, item)
                
                # Auto-resize columns
                self.results_table.resizeColumnsToContents()
                
                # Update visualization
                self.update_visualization()
                
                self.logger.info(f"Loaded {len(result.rows)} rows with {len(result.columns)} columns")
            else:
                # Show empty result message
                self.results_table.setColumnCount(1)
                self.results_table.setHorizontalHeaderLabels(["Result"])
                self.results_table.setRowCount(1)
                self.results_table.setItem(0, 0, QTableWidgetItem("No data returned"))
                self.chart_placeholder.setText("No data available for visualization")
                
        except Exception as e:
            self.logger.error(f"Error loading query results: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load query results: {str(e)}")
    
    def on_visualization_changed(self):
        """Handle visualization type change"""
        self.update_visualization()
    
    def update_visualization(self):
        """Update the chart visualization based on current data and selected type"""
        if not self.current_result or not self.current_result.rows:
            self.chart_placeholder.setText("No data available for visualization")
            self.chart_scroll.setWidget(self.chart_placeholder)
            return
        
        try:
            selected_viz = self.viz_combo.currentText().lower()
            
            # Map UI names to chart renderer names
            viz_mapping = {
                "table": "table",
                "auto-detect": None,  # Will be inferred
                "bar chart": "bar",
                "line chart": "line", 
                "pie chart": "pie",
                "scatter plot": "scatter",
                "histogram": "histogram"
            }
            
            chart_type = viz_mapping.get(selected_viz)
            
            # Generate chart
            chart_bytes = self.chart_renderer.render_chart(
                self.current_result,
                chart_type=chart_type,
                title=f"Query Results - {self.current_explanation[:50]}!" if self.current_explanation else "Query Results"
            )
            
            if chart_bytes:
                # Display chart image
                pixmap = QPixmap()
                pixmap.loadFromData(chart_bytes)
                
                chart_label = QLabel()
                chart_label.setPixmap(pixmap)
                chart_label.setAlignment(Qt.AlignCenter)
                chart_label.setScaledContents(False)
                
                self.chart_scroll.setWidget(chart_label)
                self.logger.info(f"Chart updated with type: {selected_viz}")
            else:
                self.chart_placeholder.setText(f"Unable to create {selected_viz} visualization")
                self.chart_scroll.setWidget(self.chart_placeholder)
                
        except Exception as e:
            self.logger.error(f"Error updating visualization: {e}")
            self.chart_placeholder.setText(f"Error creating visualization: {str(e)}")
            self.chart_scroll.setWidget(self.chart_placeholder)
    
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
        if not self.current_result:
            QMessageBox.warning(self, "No Data", "No query results to export.")
            return
            
        try:
            from PySide6.QtWidgets import QFileDialog
            import csv
            import os
            
            # Get export file path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Results",
                f"query_results.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if file_path:
                # Export to CSV
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write headers
                    writer.writerow(self.current_result.columns)
                    
                    # Write data rows
                    for row in self.current_result.rows:
                        writer.writerow(row)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Results exported successfully to:\n{file_path}"
                )
                self.logger.info(f"Results exported to: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export results:\n{str(e)}"
            )
