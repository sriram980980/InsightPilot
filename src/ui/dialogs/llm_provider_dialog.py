"""
LLM Provider Configuration Dialog
"""

import logging
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTextEdit, QGroupBox, QScrollArea, QWidget, QMessageBox,
    QListWidget, QListWidgetItem, QSplitter, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from llm.llm_factory import LLMClientFactory
from config.config_manager import ConfigManager


class LLMProviderDialog(QDialog):
    """Dialog for configuring LLM providers"""
    
    providers_changed = Signal()
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle("LLM Provider Configuration")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        self.load_providers()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create splitter for provider list and configuration
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side: Provider list
        self.init_provider_list(splitter)
        
        # Right side: Provider configuration
        self.init_provider_config(splitter)
        
        # Bottom buttons
        self.init_buttons(layout)
        
        # Set splitter proportions
        splitter.setSizes([250, 550])
    
    def init_provider_list(self, parent):
        """Initialize provider list widget"""
        list_widget = QWidget()
        layout = QVBoxLayout(list_widget)
        
        # Provider list
        layout.addWidget(QLabel("LLM Providers:"))
        self.provider_list = QListWidget()
        self.provider_list.currentItemChanged.connect(self.on_provider_selected)
        layout.addWidget(self.provider_list)
        
        # Provider management buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_provider)
        btn_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_provider)
        self.remove_btn.setEnabled(False)
        btn_layout.addWidget(self.remove_btn)
        
        layout.addLayout(btn_layout)
        
        parent.addWidget(list_widget)
    
    def init_provider_config(self, parent):
        """Initialize provider configuration widget"""
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)
        
        # Scroll area for configuration form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.config_form = QWidget()
        self.config_layout = QFormLayout(self.config_form)
        
        # Provider type selection
        self.provider_type = QComboBox()
        self.provider_type.addItems(["ollama", "openai", "github_copilot"])
        self.provider_type.currentTextChanged.connect(self.on_provider_type_changed)
        self.config_layout.addRow("Provider Type:", self.provider_type)
        
        # Basic configuration
        self.model_edit = QLineEdit()
        self.config_layout.addRow("Model:", self.model_edit)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.config_layout.addRow("API Key:", self.api_key_edit)
        
        self.base_url_edit = QLineEdit()
        self.config_layout.addRow("Base URL:", self.base_url_edit)
        
        # Generation parameters
        params_group = QGroupBox("Generation Parameters")
        params_layout = QFormLayout(params_group)
        
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.1)
        params_layout.addRow("Temperature:", self.temperature_spin)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 10000)
        self.max_tokens_spin.setValue(1000)
        params_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 600)
        self.timeout_spin.setValue(180)
        self.timeout_spin.setSuffix(" seconds")
        params_layout.addRow("Timeout:", self.timeout_spin)
        
        self.config_layout.addRow(params_group)
        
        # Enable/disable checkbox
        self.enabled_checkbox = QCheckBox("Enable this provider")
        self.enabled_checkbox.setChecked(True)
        self.config_layout.addRow(self.enabled_checkbox)
        
        # Test connection button
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        self.config_layout.addRow(self.test_btn)
        
        # Status label
        self.status_label = QLabel("")
        self.config_layout.addRow("Status:", self.status_label)
        
        scroll.setWidget(self.config_form)
        layout.addWidget(scroll)
        
        parent.addWidget(config_widget)
        
        # Initially disable form
        self.config_form.setEnabled(False)
    
    def init_buttons(self, layout):
        """Initialize dialog buttons"""
        button_layout = QHBoxLayout()
        
        # Default provider selection
        button_layout.addWidget(QLabel("Default Provider:"))
        self.default_provider_combo = QComboBox()
        button_layout.addWidget(self.default_provider_combo)
        
        button_layout.addStretch()
        
        # Save and Cancel buttons
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_configuration)
        button_layout.addWidget(self.save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_providers(self):
        """Load existing providers from configuration"""
        # Use LLM connections instead of deprecated llm_providers
        connections = self.config_manager.get_llm_connections()
        default_connection = self.config_manager.get_default_llm_connection()
        
        self.provider_list.clear()
        self.default_provider_combo.clear()
        
        for name, config in connections.items():
            if config.get("type") == "LLM":  # Only show LLM connections
                item = QListWidgetItem(name)
                if not config.get("enabled", True):
                    item.setForeground(Qt.gray)
                self.provider_list.addItem(item)
                self.default_provider_combo.addItem(name)
        
        # Set default provider
        if default_connection:
            index = self.default_provider_combo.findText(default_connection)
            if index >= 0:
                self.default_provider_combo.setCurrentIndex(index)
    
    def on_provider_selected(self, current, previous):
        """Handle provider selection"""
        if current is None:
            self.config_form.setEnabled(False)
            self.remove_btn.setEnabled(False)
            return
        
        self.remove_btn.setEnabled(True)
        self.config_form.setEnabled(True)
        
        # Load provider configuration
        provider_name = current.text()
        connections = self.config_manager.get_llm_connections()
        
        if provider_name in connections:
            config = connections[provider_name]
            self.load_provider_config(config)
    
    def load_provider_config(self, config: Dict[str, Any]):
        """Load provider configuration into form"""
        self.provider_type.setCurrentText(config.get("provider", "ollama"))
        self.model_edit.setText(config.get("model", ""))
        self.api_key_edit.setText(config.get("api_key", ""))
        self.base_url_edit.setText(config.get("base_url", ""))
        self.temperature_spin.setValue(config.get("temperature", 0.1))
        self.max_tokens_spin.setValue(config.get("max_tokens", 1000))
        self.timeout_spin.setValue(config.get("timeout", 180))
        self.enabled_checkbox.setChecked(config.get("enabled", True))
        
        self.on_provider_type_changed(config.get("provider", "ollama"))
    
    def on_provider_type_changed(self, provider_type: str):
        """Handle provider type change"""
        # Show/hide relevant fields based on provider type
        if provider_type == "ollama":
            self.api_key_edit.setVisible(False)
            self.config_layout.labelForField(self.api_key_edit).setVisible(False)
            self.base_url_edit.setPlaceholderText("http://localhost:11434")
            self.model_edit.setPlaceholderText("mistral:7b")
        elif provider_type == "openai":
            self.api_key_edit.setVisible(True)
            self.config_layout.labelForField(self.api_key_edit).setVisible(True)
            self.base_url_edit.setPlaceholderText("https://api.openai.com/v1")
            self.model_edit.setPlaceholderText("gpt-4o-mini")
        elif provider_type == "github_copilot":
            self.api_key_edit.setVisible(True)
            self.config_layout.labelForField(self.api_key_edit).setVisible(True)
            self.base_url_edit.setPlaceholderText("https://models.inference.ai.azure.com")
            self.model_edit.setPlaceholderText("gpt-4o")
    
    def add_provider(self):
        """Add a new provider"""
        from PySide6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "Add Provider", "Provider name:")
        if ok and name:
            # Check if name already exists
            connections = self.config_manager.get_llm_connections()
            if name in connections:
                QMessageBox.warning(self, "Error", f"Provider '{name}' already exists!")
                return
            
            # Add to list
            item = QListWidgetItem(name)
            self.provider_list.addItem(item)
            self.provider_list.setCurrentItem(item)
            self.default_provider_combo.addItem(name)
            
            # Set default configuration
            self.provider_type.setCurrentText("ollama")
            self.model_edit.setText("mistral:7b")
            self.api_key_edit.setText("")
            self.base_url_edit.setText("")
            self.temperature_spin.setValue(0.1)
            self.max_tokens_spin.setValue(1000)
            self.timeout_spin.setValue(180)
            self.enabled_checkbox.setChecked(True)
    
    def remove_provider(self):
        """Remove selected provider"""
        current_item = self.provider_list.currentItem()
        if current_item is None:
            return
        
        provider_name = current_item.text()
        
        reply = QMessageBox.question(
            self, "Confirm", 
            f"Remove provider '{provider_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from list
            row = self.provider_list.row(current_item)
            self.provider_list.takeItem(row)
            
            # Remove from default combo
            index = self.default_provider_combo.findText(provider_name)
            if index >= 0:
                self.default_provider_combo.removeItem(index)
            
            # Disable form if no items left
            if self.provider_list.count() == 0:
                self.config_form.setEnabled(False)
                self.remove_btn.setEnabled(False)
    
    def test_connection(self):
        """Test connection to the selected provider"""
        current_item = self.provider_list.currentItem()
        if current_item is None:
            return
        
        try:
            # Create temporary config
            config = self.get_current_config()
            
            # Create provider and test
            from llm.providers.base_provider import LLMConfig
            from llm.enhanced_llm_client import EnhancedLLMClient
            
            llm_config = LLMConfig(
                provider=config["provider"],
                model=config["model"],
                api_key=config.get("api_key"),
                base_url=config.get("base_url"),
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                timeout=config["timeout"]
            )
            
            client = EnhancedLLMClient({current_item.text(): llm_config})
            
            # Test health check
            if client.health_check(current_item.text()):
                self.status_label.setText("✅ Connection successful")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText("❌ Connection failed")
                self.status_label.setStyleSheet("color: red;")
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current form configuration"""
        config = {
            "provider": self.provider_type.currentText(),
            "model": self.model_edit.text(),
            "temperature": self.temperature_spin.value(),
            "max_tokens": self.max_tokens_spin.value(),
            "timeout": self.timeout_spin.value(),
            "enabled": self.enabled_checkbox.isChecked()
        }
        
        if self.api_key_edit.text():
            config["api_key"] = self.api_key_edit.text()
        if self.base_url_edit.text():
            config["base_url"] = self.base_url_edit.text()
        
        return config
    
    def save_configuration(self):
        """Save all provider configurations"""
        try:
            # Collect all provider configurations
            for i in range(self.provider_list.count()):
                item = self.provider_list.item(i)
                provider_name = item.text()
                
                # Select item to load its config
                self.provider_list.setCurrentItem(item)
                config = self.get_current_config()
                
                # Save to config manager
                self.config_manager.add_llm_provider(provider_name, config)
            
            # Set default provider
            default_provider = self.default_provider_combo.currentText()
            if default_provider:
                self.config_manager.set_default_llm_provider(default_provider)
            
            self.providers_changed.emit()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")
            self.logger.error(f"Failed to save LLM provider configuration: {e}")
