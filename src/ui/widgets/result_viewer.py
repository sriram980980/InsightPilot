"""
Result Viewer Widget - Display query results as tables and charts with enhanced zoom functionality
"""

import json
import logging
from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QTabWidget, QLabel,
    QComboBox, QGroupBox, QFormLayout, QTextEdit, QLineEdit,
    QSplitter, QMessageBox, QProgressBar, QCheckBox, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd

from adapters.base_adapter import QueryResult
from llm.llm_client import LLMClient, LLMResponse
from visualization.chart_renderer import ChartRenderer
from .enhanced_chart_widget import EnhancedChartArea


class ChartRecommendationThread(QThread):
    """Thread for getting chart recommendations from LLM"""
    
    recommendation_ready = Signal(object)  # LLMResponse
    
    def __init__(self, llm_client: LLMClient, columns: List[str], sample_data: List[List[Any]], question: str, user_hint: str = ""):
        super().__init__()
        self.llm_client = llm_client
        self.columns = columns
        self.sample_data = sample_data
        self.question = question
        self.user_hint = user_hint
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Get chart recommendation from LLM"""
        try:
            response = self.llm_client.recommend_chart(
                self.columns, 
                self.sample_data, 
                self.question, 
                self.user_hint
            )
            self.recommendation_ready.emit(response)
        except Exception as e:
            self.logger.error(f"Chart recommendation error: {e}")
            error_response = LLMResponse(
                content="",
                success=False,
                error=str(e)
            )
            self.recommendation_ready.emit(error_response)


class ResultViewer(QWidget):
    """Widget for displaying query results as tables and charts"""
    
    def __init__(self, llm_client: LLMClient = None, parent=None):
        super().__init__(parent)
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        self.chart_renderer = ChartRenderer()
        self.current_result = None
        self.current_question = ""
        self.recommendation_thread = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the result viewer UI"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_group = QGroupBox("📊 Visualization Controls")
        control_layout = QFormLayout(control_group)
        
        # Chart type selection
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "table", "bar", "line", "pie", "scatter", "histogram"
        ])
        self.chart_type_combo.currentTextChanged.connect(self.on_chart_type_changed)
        control_layout.addRow("Chart Type:", self.chart_type_combo)
        
        # Chart hint input
        self.chart_hint_input = QLineEdit()
        self.chart_hint_input.setPlaceholderText("e.g., 'show as pie chart', 'group by month', 'highlight top 5'")
        control_layout.addRow("Chart Hint:", self.chart_hint_input)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.auto_recommend_btn = QPushButton("🤖 Auto Recommend Chart")
        self.auto_recommend_btn.clicked.connect(self.auto_recommend_chart)
        self.auto_recommend_btn.setEnabled(False)
        button_layout.addWidget(self.auto_recommend_btn)
        
        self.apply_hint_btn = QPushButton("� Apply Chart Hint")
        self.apply_hint_btn.clicked.connect(self.apply_chart_hint)
        self.apply_hint_btn.setEnabled(False)
        button_layout.addWidget(self.apply_hint_btn)
        
        self.export_btn = QPushButton("💾 Export Data")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        self.save_chart_btn = QPushButton("📸 Save Chart")
        self.save_chart_btn.clicked.connect(self.save_chart)
        self.save_chart_btn.setEnabled(False)
        button_layout.addWidget(self.save_chart_btn)
        
        button_layout.addStretch()
        control_layout.addRow("", button_layout)
        
        layout.addWidget(control_group)
        
        # Progress bar for chart generation
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Result display area with tabs
        self.result_tabs = QTabWidget()
        
        # Table view tab
        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)
        self.result_tabs.addTab(self.table_widget, "📋 Table View")
        
        # Enhanced Chart view tab with zoom functionality
        self.enhanced_chart_area = EnhancedChartArea()
        self.result_tabs.addTab(self.enhanced_chart_area, "📊 Chart View (Zoomable)")
        
        layout.addWidget(self.result_tabs)
        
        # Status label
        self.status_label = QLabel("No data loaded")
        self.status_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.status_label)
    
    def load_result(self, result: QueryResult, question: str = ""):
        """Load query result into the viewer"""
        self.current_result = result
        self.current_question = question
        
        if not result or not result.rows:
            self.clear_display()
            self.status_label.setText("No data to display")
            return
        
        # Load table view
        self.load_table_view(result)
        
        # Enable controls
        self.auto_recommend_btn.setEnabled(True)
        self.apply_hint_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        # save_chart_btn will be enabled after chart generation
        
        # Update status
        self.status_label.setText(
            f"Loaded {result.row_count} rows, {len(result.columns)} columns"
        )
        
        # Auto-generate chart if LLM is available
        if self.llm_client:
            self.auto_recommend_chart()
        else:
            # If no LLM, generate a basic chart
            self.generate_chart()
    
    def load_table_view(self, result: QueryResult):
        """Load data into table widget"""
        self.table_widget.setRowCount(len(result.rows))
        self.table_widget.setColumnCount(len(result.columns))
        self.table_widget.setHorizontalHeaderLabels(result.columns)
        
        # Populate table data
        for row_idx, row_data in enumerate(result.rows):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                self.table_widget.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self.table_widget.resizeColumnsToContents()
        
        # Limit column width
        for col in range(len(result.columns)):
            if self.table_widget.columnWidth(col) > 200:
                self.table_widget.setColumnWidth(col, 200)
    
    def auto_recommend_chart(self):
        """Get automatic chart recommendation from LLM"""
        if not self.current_result or not self.llm_client:
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.auto_recommend_btn.setEnabled(False)
        
        # Get sample data for LLM
        sample_data = self.current_result.rows[:10]  # First 10 rows
        
        # Start recommendation thread
        self.recommendation_thread = ChartRecommendationThread(
            self.llm_client,
            self.current_result.columns,
            sample_data,
            self.current_question
        )
        self.recommendation_thread.recommendation_ready.connect(self.on_recommendation_ready)
        self.recommendation_thread.start()
    
    def apply_chart_hint(self):
        """Apply user chart hint using LLM"""
        if not self.current_result or not self.llm_client:
            return
        
        user_hint = self.chart_hint_input.text().strip()
        if not user_hint:
            QMessageBox.information(self, "No Hint", "Please enter a chart hint first.")
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.apply_hint_btn.setEnabled(False)
        
        # Get sample data for LLM
        sample_data = self.current_result.rows[:10]  # First 10 rows
        
        # Start recommendation thread with user hint
        self.recommendation_thread = ChartRecommendationThread(
            self.llm_client,
            self.current_result.columns,
            sample_data,
            self.current_question,
            user_hint
        )
        self.recommendation_thread.recommendation_ready.connect(self.on_recommendation_ready)
        self.recommendation_thread.start()
    
    def on_recommendation_ready(self, response: LLMResponse):
        """Handle chart recommendation from LLM"""
        # Hide progress
        self.progress_bar.setVisible(False)
        self.auto_recommend_btn.setEnabled(True)
        self.apply_hint_btn.setEnabled(True)
        
        if not response.success:
            QMessageBox.warning(self, "Recommendation Error", f"Failed to get chart recommendation: {response.error}")
            return
        
        try:
            # Parse LLM response
            recommendation = json.loads(response.content.strip())
            
            # Update chart type selection
            chart_type = recommendation.get("chart_type", "table")
            if chart_type in ["bar", "line", "pie", "scatter", "histogram", "table"]:
                index = self.chart_type_combo.findText(chart_type)
                if index >= 0:
                    self.chart_type_combo.setCurrentIndex(index)
            
            # Generate chart with recommendation
            self.generate_chart(recommendation)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse chart recommendation: {e}")
            # Fallback: use basic chart type inference
            self.generate_chart()
        
        # Clean up thread
        if self.recommendation_thread:
            self.recommendation_thread.deleteLater()
            self.recommendation_thread = None
    
    def on_chart_type_changed(self, chart_type: str):
        """Handle manual chart type selection"""
        if self.current_result:
            self.generate_chart({"chart_type": chart_type})
    
    def generate_chart(self, recommendation: Dict[str, Any] = None):
        """Generate chart based on recommendation or current selection"""
        if not self.current_result:
            return
        
        try:
            # Get chart type
            chart_type = recommendation.get("chart_type") if recommendation else self.chart_type_combo.currentText()
            
            if chart_type == "table":
                self.result_tabs.setCurrentIndex(0)  # Switch to table view
                return
            
            # Generate chart using chart renderer
            chart_bytes = self.chart_renderer.render_chart(
                self.current_result, 
                chart_type=chart_type,
                title=recommendation.get('title', f'{chart_type.title()} Chart') if recommendation else f'{chart_type.title()} Chart'
            )
            
            if chart_bytes:
                # Display chart in enhanced chart area
                self.enhanced_chart_area.display_chart(chart_bytes)
                
                # Enable save chart button
                self.save_chart_btn.setEnabled(True)
                
                # Switch to chart view
                self.result_tabs.setCurrentIndex(1)
                
                self.logger.info(f"Chart generated successfully: {chart_type}")
            else:
                self.enhanced_chart_area.show_error(f"Failed to generate {chart_type} chart")
        
        except Exception as e:
            self.logger.error(f"Chart generation error: {e}")
            self.enhanced_chart_area.show_error(f"Error generating chart: {str(e)}")
    
    def export_data(self):
        """Export current data to CSV or Excel"""
        if not self.current_result:
            return
        
        try:
            # Get export file path
            file_path, file_type = QFileDialog.getSaveFileName(
                self,
                "Export Data",
                "query_results.csv",
                "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Convert result to pandas DataFrame
            df = pd.DataFrame(self.current_result.rows, columns=self.current_result.columns)
            
            # Export based on file extension
            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
                format_name = "Excel"
            else:
                df.to_csv(file_path, index=False)
                format_name = "CSV"
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Data successfully exported to {format_name} file:\n{file_path}"
            )
            
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export data: {str(e)}"
            )
    
    def save_chart(self):
        """Save current chart as image"""
        if not self.current_result:
            return
        
        try:
            # Get save file path
            file_path, file_type = QFileDialog.getSaveFileName(
                self,
                "Save Chart",
                "chart.png",
                "PNG Files (*.png);;JPEG Files (*.jpg);;PDF Files (*.pdf);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Get current chart type
            chart_type = self.chart_type_combo.currentText()
            
            if chart_type == "table":
                QMessageBox.information(self, "No Chart", "Please select a chart type other than 'table' to save.")
                return
            
            # Generate high-resolution chart for saving
            chart_bytes = self.chart_renderer.render_chart(
                self.current_result,
                chart_type=chart_type,
                title=f'{chart_type.title()} Chart',
                dpi=300,  # High resolution
                figsize=(12, 8)  # Larger size for better quality
            )
            
            if chart_bytes:
                # Save the chart bytes directly
                with open(file_path, 'wb') as f:
                    f.write(chart_bytes)
                
                QMessageBox.information(
                    self,
                    "Chart Saved",
                    f"Chart successfully saved to:\n{file_path}"
                )
            else:
                QMessageBox.critical(self, "Save Error", "Failed to generate chart for saving.")
                
        except Exception as e:
            self.logger.error(f"Save chart error: {e}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save chart: {str(e)}"
            )
    
    def clear_display(self):
        """Clear all displays"""
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)
        
        # Clear enhanced chart area
        self.enhanced_chart_area.show_placeholder("No chart generated yet")
        
        # Disable buttons
        self.auto_recommend_btn.setEnabled(False)
        self.apply_hint_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.save_chart_btn.setEnabled(False)
        
        # Clear current data
        self.current_result = None
        self.current_question = ""
