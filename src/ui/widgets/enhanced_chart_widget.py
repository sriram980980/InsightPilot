"""
Enhanced Chart Widget with zoom and pan functionality
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QScrollArea, QSizePolicy, QToolBar, QSlider
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QPainter, QWheelEvent, QMouseEvent, QAction, QIcon

from visualization.chart_renderer import ChartRenderer


class ZoomableChartWidget(QLabel):
    """Chart widget with zoom and pan capabilities"""
    
    zoom_changed = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Zoom properties
        self._zoom_factor = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 5.0
        self._zoom_step = 0.1
        
        # Original pixmap
        self._original_pixmap = None
        self._scaled_pixmap = None
        
        # Pan properties
        self._panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0
        
        # Setup
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #cccccc;
            }
        """)
        
        # Enable mouse tracking for pan
        self.setMouseTracking(True)
    
    def setPixmap(self, pixmap: QPixmap):
        """Set the chart pixmap and reset zoom"""
        self._original_pixmap = pixmap
        self._zoom_factor = 1.0
        self._update_scaled_pixmap()
        self.fit_to_view()
    
    def _update_scaled_pixmap(self):
        """Update the scaled pixmap based on current zoom factor"""
        if self._original_pixmap is None:
            return
        
        # Calculate new size
        new_size = self._original_pixmap.size() * self._zoom_factor
        
        # Scale pixmap
        self._scaled_pixmap = self._original_pixmap.scaled(
            new_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # Set the scaled pixmap
        super().setPixmap(self._scaled_pixmap)
        self.zoom_changed.emit(self._zoom_factor)
    
    def zoom_in(self):
        """Zoom in by one step"""
        new_zoom = min(self._zoom_factor + self._zoom_step, self._max_zoom)
        self.set_zoom(new_zoom)
    
    def zoom_out(self):
        """Zoom out by one step"""
        new_zoom = max(self._zoom_factor - self._zoom_step, self._min_zoom)
        self.set_zoom(new_zoom)
    
    def set_zoom(self, zoom_factor: float):
        """Set specific zoom factor"""
        self._zoom_factor = max(self._min_zoom, min(zoom_factor, self._max_zoom))
        self._update_scaled_pixmap()
    
    def fit_to_view(self):
        """Fit chart to current widget size"""
        if self._original_pixmap is None:
            return
        
        # Get available size (minus some padding)
        available_size = self.size() - QSize(20, 20)
        pixmap_size = self._original_pixmap.size()
        
        # Calculate scale factor to fit
        scale_x = available_size.width() / pixmap_size.width()
        scale_y = available_size.height() / pixmap_size.height()
        scale_factor = min(scale_x, scale_y, 1.0)  # Don't scale up beyond 100%
        
        self.set_zoom(scale_factor)
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.set_zoom(1.0)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        if event.modifiers() & Qt.ControlModifier:
            # Zoom with Ctrl+Wheel
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for panning"""
        if event.button() == Qt.LeftButton:
            self._panning = True
            self._pan_start_x = event.x()
            self._pan_start_y = event.y()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for panning"""
        if self._panning and self._scaled_pixmap:
            # Calculate pan delta
            dx = event.x() - self._pan_start_x
            dy = event.y() - self._pan_start_y
            
            # Update pan start position
            self._pan_start_x = event.x()
            self._pan_start_y = event.y()
            
            # For now, we'll handle panning via the scroll area
            # The scroll area parent will handle the actual scrolling
        
        super().mouseMoveEvent(event)
    
    def get_zoom_factor(self) -> float:
        """Get current zoom factor"""
        return self._zoom_factor


class EnhancedChartArea(QWidget):
    """Enhanced chart area with zoom controls and scroll area"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Initialize chart renderer
        self.chart_renderer = ChartRenderer()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the enhanced chart area UI"""
        layout = QVBoxLayout(self)
        
        # Toolbar with zoom controls
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        
        # Zoom controls
        zoom_in_action = QAction("🔍+", self)
        zoom_in_action.setToolTip("Zoom In (Ctrl+Mouse Wheel)")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("🔍-", self)
        zoom_out_action.setToolTip("Zoom Out (Ctrl+Mouse Wheel)")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        fit_action = QAction("⊡", self)
        fit_action.setToolTip("Fit to View")
        fit_action.triggered.connect(self.fit_to_view)
        toolbar.addAction(fit_action)
        
        reset_action = QAction("1:1", self)
        reset_action.setToolTip("Reset Zoom (100%)")
        reset_action.triggered.connect(self.reset_zoom)
        toolbar.addAction(reset_action)
        
        toolbar.addSeparator()
        
        # Zoom level slider
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)  # 10% to 500%
        self.zoom_slider.setValue(100)
        self.zoom_slider.setToolTip("Zoom Level")
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
        toolbar.addWidget(QLabel("Zoom:"))
        toolbar.addWidget(self.zoom_slider)
        
        # Zoom percentage label
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        toolbar.addWidget(self.zoom_label)
        
        layout.addWidget(toolbar)
        
        # Scroll area with zoomable chart
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)  # Important for zoom to work
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create zoomable chart widget
        self.chart_widget = ZoomableChartWidget()
        self.chart_widget.zoom_changed.connect(self.on_zoom_changed)
        
        # Placeholder
        self.placeholder = QLabel("Chart visualization will appear here")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("""
            QLabel {
                background-color: #f8f8f8;
                border: 2px dashed #cccccc;
                border-radius: 10px;
                padding: 20px;
                color: #666666;
                font-size: 14px;
            }
        """)
        
        # Initially show placeholder
        self.scroll_area.setWidget(self.placeholder)
        layout.addWidget(self.scroll_area)
    
    def display_chart(self, chart_bytes: bytes):
        """Display chart from bytes data"""
        try:
            # Create pixmap from bytes
            pixmap = QPixmap()
            if pixmap.loadFromData(chart_bytes):
                # Set chart in zoomable widget
                self.chart_widget.setPixmap(pixmap)
                
                # Switch to chart widget
                self.scroll_area.setWidget(self.chart_widget)
                
                # Fit to view initially
                self.fit_to_view()
                
                self.logger.info("Chart displayed successfully with zoom capabilities")
            else:
                self.show_error("Failed to load chart data")
                
        except Exception as e:
            self.logger.error(f"Error displaying chart: {e}")
            self.show_error(f"Error displaying chart: {str(e)}")
    
    def show_placeholder(self, message: str = "Chart visualization will appear here"):
        """Show placeholder message"""
        self.placeholder.setText(message)
        self.scroll_area.setWidget(self.placeholder)
    
    def show_error(self, message: str):
        """Show error message"""
        self.placeholder.setText(f"Error: {message}")
        self.placeholder.setStyleSheet("""
            QLabel {
                background-color: #ffe6e6;
                border: 2px dashed #ff9999;
                border-radius: 10px;
                padding: 20px;
                color: #cc0000;
                font-size: 14px;
            }
        """)
        self.scroll_area.setWidget(self.placeholder)
    
    def zoom_in(self):
        """Zoom in the chart"""
        if isinstance(self.scroll_area.widget(), ZoomableChartWidget):
            self.chart_widget.zoom_in()
    
    def zoom_out(self):
        """Zoom out the chart"""
        if isinstance(self.scroll_area.widget(), ZoomableChartWidget):
            self.chart_widget.zoom_out()
    
    def fit_to_view(self):
        """Fit chart to view"""
        if isinstance(self.scroll_area.widget(), ZoomableChartWidget):
            self.chart_widget.fit_to_view()
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if isinstance(self.scroll_area.widget(), ZoomableChartWidget):
            self.chart_widget.reset_zoom()
    
    def on_zoom_slider_changed(self, value: int):
        """Handle zoom slider change"""
        if isinstance(self.scroll_area.widget(), ZoomableChartWidget):
            zoom_factor = value / 100.0
            self.chart_widget.set_zoom(zoom_factor)
    
    def on_zoom_changed(self, zoom_factor: float):
        """Handle zoom change from chart widget"""
        # Update slider without triggering signal
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(zoom_factor * 100))
        self.zoom_slider.blockSignals(False)
        
        # Update label
        self.zoom_label.setText(f"{int(zoom_factor * 100)}%")
