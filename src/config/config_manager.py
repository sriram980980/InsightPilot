"""
Secure configuration management with encryption
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from cryptography.fernet import Fernet
import keyring

from adapters.base_adapter import DBConnection


class ConfigManager:
    """Secure configuration manager with encryption"""
    
    SERVICE_NAME = "InsightPilot"
    KEY_NAME = "config_encryption_key"
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path or self._get_default_config_path())
        self._cipher = None
        self._config = {}
        self._initialize_encryption()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        if os.name == 'nt':  # Windows
            config_dir = Path.home() / "AppData" / "Local" / "InsightPilot"
        else:  # Unix-like
            config_dir = Path.home() / ".config" / "insightpilot"
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / "config.encrypted")
    
    def _initialize_encryption(self) -> None:
        """Initialize encryption using keyring"""
        try:
            # Try to get existing key from keyring
            key = keyring.get_password(self.SERVICE_NAME, self.KEY_NAME)
            
            if key is None:
                # Generate new key if none exists
                key = Fernet.generate_key().decode()
                keyring.set_password(self.SERVICE_NAME, self.KEY_NAME, key)
                self.logger.info("Generated new encryption key")
            
            self._cipher = Fernet(key.encode())
            
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def _load_config(self) -> None:
        """Load configuration from encrypted file"""
        try:
            if not self.config_path.exists():
                self._config = self._get_default_config()
                self._save_config()
                return
            
            with open(self.config_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._cipher.decrypt(encrypted_data)
            self._config = json.loads(decrypted_data.decode())
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._config = self._get_default_config()
    
    def _save_config(self) -> None:
        """Save configuration to encrypted file"""
        try:
            config_json = json.dumps(self._config, indent=2)
            encrypted_data = self._cipher.encrypt(config_json.encode())
            
            with open(self.config_path, 'wb') as f:
                f.write(encrypted_data)
            
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "database_connections": {},
            "llm_settings": {
                "model": "mistral:7b",
                "host": "localhost",
                "port": 11434,
                "temperature": 0.1,
                "max_tokens": 1000
            },
            "ui_settings": {
                "theme": "light",
                "font_size": 12,
                "auto_save": True
            },
            "security": {
                "query_timeout": 30,
                "max_rows": 1000,
                "max_query_history": 100
            },
            "export_settings": {
                "default_format": "csv",
                "chart_dpi": 300
            }
        }
    
    def get_database_connections(self) -> Dict[str, DBConnection]:
        """Get all database connections"""
        connections = {}
        
        for name, config in self._config.get("database_connections", {}).items():
            connections[name] = DBConnection(
                host=config["host"],
                port=config["port"],
                database=config["database"],
                username=config["username"],
                password=config["password"],
                connection_params=config.get("connection_params")
            )
        
        return connections
    
