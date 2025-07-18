"""
LLM Connection Dialog - LLM server configuration
"""

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox,
    QGroupBox, QMessageBox, QCheckBox, QTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from llm.llm_client import LLMClient


class LLMTestThread(QThread):
    """Thread for testing LLM connections"""
    result_ready = Signal(bool, str)
    progress_update = Signal(str)
    
    def __init__(self, llm_config):
        super().__init__()
        self.llm_config = llm_config
        
    def run(self):
        """Test the LLM connection"""
        try:
            self.progress_update.emit("Connecting to LLM server...")
            
            # Create LLM client
            client = LLMClient(
                host=self.llm_config['host'],
                port=self.llm_config['port'],
                model=self.llm_config['model']
            )
            
            # Test health check
            self.progress_update.emit("Checking server health...")
            if not client.health_check():
                self.result_ready.emit(False, "LLM server is not running or unreachable")
                return
            
            # Test model availability
            self.progress_update.emit("Checking model availability...")
            models = client.list_models()
            available_models = [model["name"] for model in models.get("models", [])]
            
            if self.llm_config['model'] not in available_models:
                self.result_ready.emit(False, f"Model '{self.llm_config['model']}' not found. Available models: {', '.join(available_models)}")
                return
            
            # Test generation
            self.progress_update.emit("Testing text generation...")
            response = client.generate("Hello, this is a test prompt.")
            
            if response.success:
                self.result_ready.emit(True, f"LLM connection successful! Generated {response.tokens_used} tokens.")
            else:
                self.result_ready.emit(False, f"Generation test failed: {response.error}")
                
        except Exception as e:
            self.result_ready.emit(False, f"LLM connection test error: {str(e)}")


class LLMConnectionDialog(QDialog):
    """Dialog for creating/editing LLM connections"""
    
    def __init__(self, config_manager, connection_name=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.connection_name = connection_name
        self.logger = logging.getLogger(__name__)
        self.test_thread = None
        
        self.setWindowTitle("Setup LLM Connection" if not connection_name else f"Edit LLM Connection: {connection_name}")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        
        if connection_name:
            self.load_connection_config()
    
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Connection name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Connection Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Local Ollama, Remote LLM Server")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # LLM Server Configuration
        server_group = QGroupBox("LLM Server Configuration")
        server_layout = QFormLayout(server_group)
        
        # Host
        self.host_edit = QLineEdit("localhost")
        server_layout.addRow("Host:", self.host_edit)
        
        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(11434)
        server_layout.addRow("Port:", self.port_spin)
        
        # Model
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems([
            "mistral:7b",
            "llama2:7b",
            "codellama:7b",
            "phi:2.7b",
            "neural-chat:7b"
        ])
        server_layout.addRow("Model:", self.model_combo)
        
        # Load models button
        self.load_models_btn = QPushButton("Load Available Models")
        self.load_models_btn.clicked.connect(self.load_available_models)
        server_layout.addRow("", self.load_models_btn)
        
        layout.addWidget(server_group)
        
        # Generation Parameters
        params_group = QGroupBox("Generation Parameters")
        params_layout = QFormLayout(params_group)
        
        # Temperature
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(0, 100)
        self.temperature_spin.setValue(10)
        self.temperature_spin.setSuffix(" (0.1)")
        params_layout.addRow("Temperature:", self.temperature_spin)
        
        # Max Tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 8000)
        self.max_tokens_spin.setValue(1000)
        params_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        layout.addWidget(params_group)
        
        # Test section
        test_group = QGroupBox("Connection Test")
        test_layout = QVBoxLayout(test_group)
        
        # Test button and progress
        test_button_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        test_button_layout.addWidget(self.test_btn)
        test_button_layout.addStretch()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        test_button_layout.addWidget(self.progress_bar)
        
        test_layout.addLayout(test_button_layout)
        
        # Test results
        self.test_result = QTextEdit()
        self.test_result.setMaximumHeight(80)
        self.test_result.setReadOnly(True)
        test_layout.addWidget(self.test_result)
        
        layout.addWidget(test_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_connection)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def load_available_models(self):
        """Load available models from the LLM server"""
        try:
            client = LLMClient(
                host=self.host_edit.text(),
                port=self.port_spin.value()
            )
            
            if not client.health_check():
                QMessageBox.warning(self, "Connection Error", "Cannot connect to LLM server. Please check host and port.")
                return
            
            models = client.list_models()
            available_models = [model["name"] for model in models.get("models", [])]
            
            if available_models:
                self.model_combo.clear()
                self.model_combo.addItems(available_models)
                QMessageBox.information(self, "Success", f"Loaded {len(available_models)} models from server.")
            else:
                QMessageBox.warning(self, "No Models", "No models found on the server.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load models: {str(e)}")
    
    def test_connection(self):
        """Test the LLM connection"""
        if self.test_thread and self.test_thread.isRunning():
            return
        
        config = {
            'host': self.host_edit.text(),
            'port': self.port_spin.value(),
            'model': self.model_combo.currentText(),
            'temperature': self.temperature_spin.value() / 100.0,
            'max_tokens': self.max_tokens_spin.value()
        }
        
        self.test_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.test_result.clear()
        
        self.test_thread = LLMTestThread(config)
        self.test_thread.result_ready.connect(self.on_test_result)
        self.test_thread.progress_update.connect(self.on_progress_update)
        self.test_thread.start()
    
    def on_progress_update(self, message):
        """Handle progress updates"""
        self.test_result.append(message)
    
    def on_test_result(self, success, message):
        """Handle test results"""
        self.test_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.test_result.append(f"✓ {message}")
            self.test_result.setStyleSheet("color: green;")
        else:
            self.test_result.append(f"✗ {message}")
            self.test_result.setStyleSheet("color: red;")
    
    def save_connection(self):
        """Save the LLM connection"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Connection name is required.")
            return
        
        config = {
            'type': 'LLM',
            'host': self.host_edit.text(),
            'port': self.port_spin.value(),
            'model': self.model_combo.currentText(),
            'temperature': self.temperature_spin.value() / 100.0,
            'max_tokens': self.max_tokens_spin.value()
        }
        
        try:
            # Save to config manager
            self.config_manager.save_connection(name, config)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save connection: {str(e)}")
    
    def load_connection_config(self):
        """Load existing connection configuration"""
        try:
            connections = self.config_manager.get_connections()
            if self.connection_name in connections:
                config = connections[self.connection_name]
                
                self.name_edit.setText(self.connection_name)
                self.host_edit.setText(config.get('host', 'localhost'))
                self.port_spin.setValue(config.get('port', 11434))
                self.model_combo.setCurrentText(config.get('model', 'mistral:7b'))
                self.temperature_spin.setValue(int(config.get('temperature', 0.1) * 100))
                self.max_tokens_spin.setValue(config.get('max_tokens', 1000))
                
        except Exception as e:
            self.logger.error(f"Error loading connection config: {e}")
