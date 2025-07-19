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
    
    def __init__(self, llm_config, provider_sub_type="ollama"):
        super().__init__()
        self.llm_config = llm_config
        self.provider_sub_type = provider_sub_type
        
    def run(self):
        """Test the LLM connection"""
        try:
            self.progress_update.emit(f"Testing {self.provider_sub_type.upper()} connection!")
            
            if self.provider_sub_type == "ollama":
                self._test_ollama()
            elif self.provider_sub_type == "openai":
                self._test_openai()
            elif self.provider_sub_type == "github":
                self._test_github_copilot()
            else:
                self.result_ready.emit(False, f"Unsupported provider sub-type: {self.provider_sub_type}")
                
        except Exception as e:
            self.result_ready.emit(False, f"Connection test error: {str(e)}")
    
    def _test_ollama(self):
        """Test Ollama connection"""
        try:
            # Validate required config fields first
            required_fields = ['host', 'port', 'model']
            missing_fields = [field for field in required_fields if field not in self.llm_config]
            if missing_fields:
                self.result_ready.emit(False, f"Missing required config fields: {', '.join(missing_fields)}")
                return
            
            # Create LLM client
            client = LLMClient(
                host=self.llm_config['host'],
                port=self.llm_config['port'],
                model=self.llm_config['model']
            )
            
            # Test health check
            self.progress_update.emit("Checking Ollama server health!")
            if not client.health_check():
                self.result_ready.emit(False, "Ollama server is not running or unreachable")
                return
            
            # Test model availability
            self.progress_update.emit("Checking model availability!")
            models = client.list_models()
            available_models = [model["name"] for model in models.get("models", [])]
            
            if self.llm_config['model'] not in available_models:
                self.result_ready.emit(False, f"Model '{self.llm_config['model']}' not found. Available models: {', '.join(available_models)}")
                return
            
            # Test generation
            self.progress_update.emit("Testing text generation!")
            response = client.generate("Hello, this is a test prompt.")
            
            if response.success:
                self.result_ready.emit(True, f"Ollama connection successful! Generated {response.tokens_used} tokens.")
            else:
                self.result_ready.emit(False, f"Generation test failed: {response.error}")
                
        except Exception as e:
            self.result_ready.emit(False, f"Ollama test error: {str(e)}")
    
    def _test_openai(self):
        """Test OpenAI connection"""
        try:
            from llm.providers.openai_provider import OpenAIProvider
            from llm.providers.base_provider import LLMConfig
            
            # Validate required config fields first
            required_fields = ['model', 'api_key', 'base_url', 'temperature', 'max_tokens', 'timeout']
            missing_fields = [field for field in required_fields if field not in self.llm_config]
            if missing_fields:
                self.result_ready.emit(False, f"Missing required config fields: {', '.join(missing_fields)}")
                return
            
            config = LLMConfig(
                provider="openai",
                model=self.llm_config['model'],
                api_key=self.llm_config['api_key'],
                base_url=self.llm_config['base_url'],
                temperature=self.llm_config['temperature'],
                max_tokens=self.llm_config['max_tokens'],
                timeout=self.llm_config['timeout']
            )
            
            provider = OpenAIProvider(config)
            
            # Test health check
            self.progress_update.emit("Testing OpenAI API access!")
            if not provider.health_check():
                self.result_ready.emit(False, "Cannot access OpenAI API. Please check your API key.")
                return
            
            # Test generation
            self.progress_update.emit("Testing text generation with OpenAI!")
            response = provider.generate("Hello, this is a test prompt.")
            
            if response.success:
                self.result_ready.emit(True, f"OpenAI connection successful! Generated {response.tokens_used} tokens using {response.model}.")
            else:
                self.result_ready.emit(False, f"Generation test failed: {response.error}")
                
        except Exception as e:
            self.result_ready.emit(False, f"OpenAI test error: {str(e)}")
    
    def _test_github_copilot(self):
        """Test GitHub Copilot connection"""
        try:
            from llm.providers.github_copilot_provider import GitHubCopilotProvider
            from llm.providers.base_provider import LLMConfig
            
            # Validate required config fields first
            required_fields = ['model', 'api_key', 'base_url', 'temperature', 'max_tokens', 'timeout']
            missing_fields = [field for field in required_fields if field not in self.llm_config]
            if missing_fields:
                self.result_ready.emit(False, f"Missing required config fields: {', '.join(missing_fields)}")
                return
            
            config = LLMConfig(
                provider="github_copilot",
                model=self.llm_config['model'],
                api_key=self.llm_config['api_key'],
                base_url=self.llm_config['base_url'],
                temperature=self.llm_config['temperature'],
                max_tokens=self.llm_config['max_tokens'],
                timeout=self.llm_config['timeout']
            )
            
            provider = GitHubCopilotProvider(config)
            
            # Test health check
            self.progress_update.emit("Testing GitHub Copilot API access!")
            if not provider.health_check():
                self.result_ready.emit(False, "Cannot access GitHub Copilot API. Please check your token and subscription.")
                return
            
            # Test generation
            self.progress_update.emit("Testing text generation with GitHub Copilot!")
            response = provider.generate("Hello, this is a test prompt.")
            
            if response.success:
                self.result_ready.emit(True, f"GitHub Copilot connection successful! Generated {response.tokens_used} tokens using {response.model}.")
            else:
                self.result_ready.emit(False, f"Generation test failed: {response.error}")
                
        except Exception as e:
            self.result_ready.emit(False, f"GitHub Copilot test error: {str(e)}")


class LLMConnectionDialog(QDialog):
    """Dialog for creating/editing LLM connections"""
    
    def __init__(self, config_manager, connection_name=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.connection_name = connection_name
        self.logger = logging.getLogger(__name__)
        self.test_thread = None
        self._github_copilot_info_shown = False  # Track if we've shown the info dialog
        
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
        self.name_edit.setPlaceholderText("e.g., Local Ollama, OpenAI GPT-4, GitHub Copilot")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Provider Type Selection
        provider_group = QGroupBox("LLM Provider Configuration")
        self.provider_layout = QFormLayout(provider_group)
        
        # Provider sub-type
        self.provider_type = QComboBox()
        self.provider_type.addItems(["ollama", "openai", "github"])
        self.provider_type.currentTextChanged.connect(self.on_provider_type_changed)
        self.provider_layout.addRow("Provider Sub-Type:", self.provider_type)
        
        # API Key (for external providers)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter your API key or GitHub token")
        self.provider_layout.addRow("API Key:", self.api_key_edit)
        
        # Base URL
        self.base_url_edit = QLineEdit()
        self.provider_layout.addRow("Base URL:", self.base_url_edit)
        
        # Host (for Ollama)
        self.host_edit = QLineEdit("localhost")
        self.provider_layout.addRow("Host:", self.host_edit)
        
        # Port (for Ollama)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(11434)
        self.provider_layout.addRow("Port:", self.port_spin)
        
        # Model
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.provider_layout.addRow("Model:", self.model_combo)
        
        # Load models button
        self.load_models_btn = QPushButton("Load Available Models")
        self.load_models_btn.clicked.connect(self.load_available_models)
        self.provider_layout.addRow("", self.load_models_btn)
        
        layout.addWidget(provider_group)
        
        # Generation Parameters
        params_group = QGroupBox("Generation Parameters")
        params_layout = QFormLayout(params_group)
        
        # Temperature
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(0, 200)
        self.temperature_spin.setValue(10)
        self.temperature_spin.setSuffix("%")
        params_layout.addRow("Temperature:", self.temperature_spin)
        
        # Max Tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 10000)
        self.max_tokens_spin.setValue(1000)
        params_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 600)
        self.timeout_spin.setValue(180)
        self.timeout_spin.setSuffix(" seconds")
        params_layout.addRow("Timeout:", self.timeout_spin)
        
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
        
        # Initialize provider-specific settings
        self.on_provider_type_changed("ollama")
    
    def on_provider_type_changed(self, provider_type: str):
        """Handle provider type change"""
        # Clear current models
        self.model_combo.clear()
        
        if provider_type == "ollama":
            # Show Ollama-specific fields
            self.api_key_edit.setVisible(False)
            self.host_edit.setVisible(True)
            self.port_spin.setVisible(True)
            self.base_url_edit.setVisible(False)
            
            # Hide labels for invisible fields
            for i in range(self.provider_layout.rowCount()):
                label = self.provider_layout.itemAt(i, QFormLayout.LabelRole)
                if label and label.widget():
                    label_text = label.widget().text()
                    if "API Key:" in label_text:
                        label.widget().setVisible(False)
                    elif "Base URL:" in label_text:
                        label.widget().setVisible(False)
                    else:
                        label.widget().setVisible(True)
            
            # Set Ollama defaults
            self.base_url_edit.setText("")
            self.model_combo.addItems([
                "mistral:7b",
                "llama2:7b", 
                "codellama:7b",
                "phi:2.7b",
                "neural-chat:7b"
            ])
            self.load_models_btn.setText("Load Available Models")
            
        elif provider_type == "openai":
            # Show OpenAI-specific fields
            self.api_key_edit.setVisible(True)
            self.host_edit.setVisible(False)
            self.port_spin.setVisible(False)
            self.base_url_edit.setVisible(True)
            
            # Show labels for visible fields
            for i in range(self.provider_layout.rowCount()):
                label = self.provider_layout.itemAt(i, QFormLayout.LabelRole)
                if label and label.widget():
                    label_text = label.widget().text()
                    if "Host:" in label_text or "Port:" in label_text:
                        label.widget().setVisible(False)
                    else:
                        label.widget().setVisible(True)
            
            # Set OpenAI defaults
            self.base_url_edit.setText("https://api.openai.com/v1")
            self.base_url_edit.setPlaceholderText("https://api.openai.com/v1")
            self.api_key_edit.setPlaceholderText("Enter your OpenAI API key")
            self.model_combo.addItems([
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo"
            ])
            self.load_models_btn.setText("Load OpenAI Models")
            
        elif provider_type == "github":
            # Show GitHub Copilot-specific fields
            self.api_key_edit.setVisible(True)
            self.host_edit.setVisible(False)
            self.port_spin.setVisible(False)
            self.base_url_edit.setVisible(True)
            
            # Show labels for visible fields
            for i in range(self.provider_layout.rowCount()):
                label = self.provider_layout.itemAt(i, QFormLayout.LabelRole)
                if label and label.widget():
                    label_text = label.widget().text()
                    if "Host:" in label_text or "Port:" in label_text:
                        label.widget().setVisible(False)
                    else:
                        label.widget().setVisible(True)
            
            # Set GitHub Copilot defaults
            self.base_url_edit.setText("https://models.inference.ai.azure.com")
            self.base_url_edit.setPlaceholderText("https://models.inference.ai.azure.com")
            self.api_key_edit.setPlaceholderText("Enter GitHub Personal Access Token (requires Copilot subscription)")
            self.model_combo.addItems([
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-3.5-turbo"  # More likely to be available
            ])
            self.load_models_btn.setText("Load Available Models")
            
            # Show information about GitHub Copilot limitations (once per session)
            if not self._github_copilot_info_shown:
                self._github_copilot_info_shown = True
                from PySide6.QtWidgets import QCheckBox
                
                msg = QMessageBox(self)
                msg.setWindowTitle("GitHub Copilot Setup")
                msg.setIcon(QMessageBox.Information)
                msg.setText(
                    "⚠️ GitHub Copilot API Access\n\n"
                    "GitHub Copilot's chat API is not publicly available like OpenAI's API. "
                    "This connection may not work for all users.\n\n"
                    "Requirements:\n"
                    "• Active GitHub Copilot subscription\n"
                    "• GitHub Personal Access Token\n"
                    "• Special API permissions (may be required)\n\n"
                )
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
    
    def load_available_models(self):
        """Load available models from the provider"""
        provider_type = self.provider_type.currentText()
        
        try:
            if provider_type == "ollama":
                self._load_ollama_models()
            elif provider_type == "openai":
                self._load_openai_models()
            elif provider_type == "github_copilot":
                self._load_github_copilot_models()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load models: {str(e)}")
    
    def _load_ollama_models(self):
        """Load Ollama models"""
        client = LLMClient(
            host=self.host_edit.text(),
            port=self.port_spin.value()
        )
        
        if not client.health_check():
            QMessageBox.warning(self, "Connection Error", "Cannot connect to Ollama server. Please check host and port.")
            return
        
        models = client.list_models()
        available_models = [model["name"] for model in models.get("models", [])]
        
        if available_models:
            self.model_combo.clear()
            self.model_combo.addItems(available_models)
            QMessageBox.information(self, "Success", f"Loaded {len(available_models)} models from Ollama server.")
        else:
            QMessageBox.warning(self, "No Models", "No models found on the Ollama server.")
    
    def _load_openai_models(self):
        """Load OpenAI models"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "API Key Required", "Please enter your OpenAI API key first.")
            return
        
        # Use the OpenAI provider to load models
        from llm.providers.openai_provider import OpenAIProvider
        from llm.providers.base_provider import LLMConfig
        
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            api_key=api_key,
            base_url=self.base_url_edit.text() or "https://api.openai.com/v1"
        )
        
        provider = OpenAIProvider(config)
        if provider.health_check():
            models = provider.list_models()
            available_models = []
            for model in models.get("models", []):
                # Use name or friendly_name for display, but store id as value
                display_name = model.get("friendly_name") or model.get("name") or model.get("id", "")
                model_id = model.get("id", display_name)
                if display_name:
                    available_models.append((display_name, model_id))
            
            if available_models:
                self.model_combo.clear()
                for display_name, model_id in available_models:
                    self.model_combo.addItem(display_name, model_id)
                QMessageBox.information(self, "Success", f"Loaded {len(available_models)} OpenAI models.")
            else:
                QMessageBox.warning(self, "No Models", "No models available for your OpenAI account.")
        else:
            QMessageBox.warning(self, "Connection Error", "Cannot connect to OpenAI. Please check your API key.")
    
    def _load_github_copilot_models(self):
        """Load GitHub Copilot models"""
        token = self.api_key_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Token Required", "Please enter your GitHub Personal Access Token first.")
            return
        
        # Use the GitHub Copilot provider to load models
        from llm.providers.github_copilot_provider import GitHubCopilotProvider
        from llm.providers.base_provider import LLMConfig
        
        config = LLMConfig(
            provider="github_copilot",
            model="gpt-4o",
            api_key=token,
            base_url=self.base_url_edit.text() or "https://models.inference.ai.azure.com"
        )
        
        provider = GitHubCopilotProvider(config)
        if provider.health_check():
            models = provider.list_models()
            available_models = []
            for model in models.get("models", []):
                # Use friendly_name or name for display, but store id as value
                display_name = model.get("friendly_name") or model.get("name") or model.get("id", "")
                model_id = model.get("id", display_name)
                if display_name:
                    available_models.append((display_name, model_id))
            
            if available_models:
                self.model_combo.clear()
                for display_name, model_id in available_models:
                    self.model_combo.addItem(display_name, model_id)
                QMessageBox.information(self, "Success", f"Loaded {len(available_models)} GitHub Copilot models.")
            else:
                # Use supported models as fallback
                QMessageBox.information(self, "Models Available", "Using supported model list.")
        else:
            QMessageBox.warning(
                self, 
                "GitHub Copilot Access", 
                "Cannot connect to GitHub Copilot API. This may be due to:\n\n"
                "1. GitHub Personal Access Token is invalid\n"
                "2. No active GitHub Copilot subscription\n"
                "3. GitHub Copilot API requires special permissions\n\n"
                "Note: GitHub Copilot's chat API is not publicly available like OpenAI's API. "
                ""
            )
    
    def test_connection(self):
        """Test the LLM connection"""
        if self.test_thread and self.test_thread.isRunning():
            return
        
        provider_sub_type = self.provider_type.currentText()
        config = self._get_current_config()
        
        self.test_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.test_result.clear()
        
        self.test_thread = LLMTestThread(config, provider_sub_type)
        self.test_thread.result_ready.connect(self.on_test_result)
        self.test_thread.progress_update.connect(self.on_progress_update)
        
        self.test_thread.start()
    
    def _get_current_config(self):
        """Get current configuration based on provider sub-type"""
        provider_sub_type = self.provider_type.currentText()
        
        # Get model ID from combo box data, fallback to text if no data stored
        model_id = self.model_combo.currentData()
        if model_id is None:
            model_id = self.model_combo.currentText()
        
        config = {
            'sub_type': provider_sub_type,  # Use sub_type
            'model': model_id,
            'temperature': self.temperature_spin.value() / 100.0,
            'max_tokens': self.max_tokens_spin.value(),
            'timeout': self.timeout_spin.value()
        }
        
        if provider_sub_type == "ollama":
            config.update({
                'host': self.host_edit.text(),
                'port': self.port_spin.value(),
                'base_url': f"http://{self.host_edit.text()}:{self.port_spin.value()}"
            })
        elif provider_sub_type == "github":
            config.update({
                'api_key': self.api_key_edit.text(),  # Use api_key consistently
                'base_url': self.base_url_edit.text()
            })
        else:  # openai
            config.update({
                'api_key': self.api_key_edit.text(),
                'base_url': self.base_url_edit.text()
            })
        
        return config
    
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
        """Save the LLM connection with new type/sub-type structure"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Connection name is required.")
            return
        
        provider_sub_type = self.provider_type.currentText()
        
        # Validation based on provider sub-type
        if provider_sub_type in ["openai", "github"] and not self.api_key_edit.text().strip():
            provider_name = "OpenAI API key" if provider_sub_type == "openai" else "GitHub Personal Access Token"
            QMessageBox.warning(self, "Validation Error", f"{provider_name} is required.")
            return
        
        # Get model ID from combo box data, fallback to text if no data stored
        model_id = self.model_combo.currentData()
        if model_id is None:
            model_id = self.model_combo.currentText()
        
        config = {
            'type': 'LLM',  # New connection type
            'sub_type': provider_sub_type,  # New sub-type field
            'model': model_id,
            'temperature': self.temperature_spin.value() / 100.0,
            'max_tokens': self.max_tokens_spin.value(),
            'timeout': self.timeout_spin.value(),
            'enabled': True  # Default to enabled
        }
        
        if provider_sub_type == "ollama":
            config.update({
                'host': self.host_edit.text(),
                'port': self.port_spin.value()
            })
        elif provider_sub_type == "openai":
            config.update({
                'api_key': self.api_key_edit.text(),
                'base_url': self.base_url_edit.text() or "https://api.openai.com/v1"
            })
        elif provider_sub_type == "github":
            config.update({
                'api_key': self.api_key_edit.text(),  # Use api_key consistently
                'base_url': self.base_url_edit.text() or "https://models.inference.ai.azure.com"
            })
        
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
                
                # Set provider sub-type first - handle both old and new config formats
                provider_sub_type = config.get('sub_type') or config.get('provider', 'ollama')
                
                # Map old provider names to new sub-types
                if provider_sub_type == 'github_copilot':
                    provider_sub_type = 'github'
                
                self.provider_type.setCurrentText(provider_sub_type)
                self.on_provider_type_changed(provider_sub_type)
                
                # Set common fields
                stored_model = config.get('model', '')
                
                # Try to find the model in the combo box (either by display name or stored data)
                model_index = -1
                for i in range(self.model_combo.count()):
                    # Check if stored model matches the data (ID) or text (display name)
                    if (self.model_combo.itemData(i) == stored_model or 
                        self.model_combo.itemText(i) == stored_model):
                        model_index = i
                        break
                
                if model_index >= 0:
                    self.model_combo.setCurrentIndex(model_index)
                else:
                    # If not found, set as editable text (for custom models)
                    self.model_combo.setCurrentText(stored_model)
                
                self.temperature_spin.setValue(int(config.get('temperature', 0.1) * 100))
                self.max_tokens_spin.setValue(config.get('max_tokens', 1000))
                self.timeout_spin.setValue(config.get('timeout', 180))
                
                # Set provider-specific fields
                if provider_sub_type == "ollama":
                    self.host_edit.setText(config.get('host', 'localhost'))
                    self.port_spin.setValue(config.get('port', 11434))
                elif provider_sub_type == "github":
                    # Handle both old 'token' field and new 'api_key' field for backward compatibility
                    self.api_key_edit.setText(config.get('api_key') or config.get('token', ''))
                    self.base_url_edit.setText(config.get('base_url', ''))
                else:  # openai
                    self.api_key_edit.setText(config.get('api_key', ''))
                    self.base_url_edit.setText(config.get('base_url', ''))
                
        except Exception as e:
            self.logger.error(f"Error loading connection config: {e}")
