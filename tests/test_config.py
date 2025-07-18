"""
Tests for configuration management
"""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from config.config_manager import ConfigManager
from adapters.base_adapter import DBConnection


class TestConfigManager:
    """Test configuration manager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create temporary config file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.encrypted")
        
        # Mock keyring to avoid system keyring dependencies
        with patch('config.config_manager.keyring') as mock_keyring:
            mock_keyring.get_password.return_value = None
            mock_keyring.set_password.return_value = None
            # Mock the Fernet key generation
            with patch('config.config_manager.Fernet.generate_key') as mock_gen_key:
                mock_gen_key.return_value = b'test_key_32_bytes_long_for_fernet'
                with patch('config.config_manager.Fernet') as mock_fernet:
                    mock_cipher = Mock()
                    mock_fernet.return_value = mock_cipher
                    mock_cipher.encrypt.return_value = b'encrypted_data'
                    mock_cipher.decrypt.return_value = b'{"database_connections": {}}'
                    
                    self.config_manager = ConfigManager(config_path=self.config_path)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def test_default_config_structure(self):
        """Test default configuration structure"""
        config = self.config_manager.get_config()
        
        required_keys = ["database_connections", "llm_settings", "ui_settings", "security", "export_settings"]
        
        for key in required_keys:
            assert key in config
        
        assert "model" in config["llm_settings"]
        assert "host" in config["llm_settings"]
        assert "port" in config["llm_settings"]
        assert "theme" in config["ui_settings"]
        assert "query_timeout" in config["security"]
        assert "max_rows" in config["security"]
    
    def test_add_database_connection(self):
        """Test adding database connection"""
        connection = DBConnection(
            host="localhost",
            port=3306,
            database="testdb",
            username="user",
            password="pass"
        )
        
        with patch.object(self.config_manager, '_save_config') as mock_save:
            self.config_manager.add_database_connection("test_conn", connection)
            
            connections = self.config_manager.get_database_connections()
            assert "test_conn" in connections
            assert connections["test_conn"].host == "localhost"
            assert connections["test_conn"].port == 3306
            assert connections["test_conn"].database == "testdb"
            mock_save.assert_called_once()
    
    def test_remove_database_connection(self):
        """Test removing database connection"""
        # First add a connection
        connection = DBConnection(
            host="localhost",
            port=3306,
            database="testdb",
            username="user",
            password="pass"
        )
        
        with patch.object(self.config_manager, '_save_config') as mock_save:
            self.config_manager.add_database_connection("test_conn", connection)
            self.config_manager.remove_database_connection("test_conn")
            
            connections = self.config_manager.get_database_connections()
            assert "test_conn" not in connections
            assert mock_save.call_count == 2  # Once for add, once for remove
    
    def test_update_llm_settings(self):
        """Test updating LLM settings"""
        new_settings = {
            "model": "llama3:8b",
            "temperature": 0.5,
            "max_tokens": 2000
        }
        
        with patch.object(self.config_manager, '_save_config') as mock_save:
            self.config_manager.update_llm_settings(new_settings)
            
            llm_settings = self.config_manager.get_llm_settings()
            assert llm_settings["model"] == "llama3:8b"
            assert llm_settings["temperature"] == 0.5
            assert llm_settings["max_tokens"] == 2000
            mock_save.assert_called_once()
    
    def test_update_ui_settings(self):
        """Test updating UI settings"""
        new_settings = {
            "theme": "dark",
            "font_size": 14
        }
        
        with patch.object(self.config_manager, '_save_config') as mock_save:
            self.config_manager.update_ui_settings(new_settings)
            
            ui_settings = self.config_manager.get_ui_settings()
            assert ui_settings["theme"] == "dark"
            assert ui_settings["font_size"] == 14
            mock_save.assert_called_once()
    
    def test_update_security_settings(self):
        """Test updating security settings"""
        new_settings = {
            "query_timeout": 100,
            "max_rows": 5000
        }
        
        with patch.object(self.config_manager, '_save_config') as mock_save:
            self.config_manager.update_security_settings(new_settings)
            
            security_settings = self.config_manager.get_security_settings()
            assert security_settings["query_timeout"] == 100
            assert security_settings["max_rows"] == 5000
            mock_save.assert_called_once()
    
    def test_reset_config(self):
        """Test configuration reset"""
        # Modify some settings first
        self.config_manager.update_llm_settings({"model": "custom:model"})
        
        with patch.object(self.config_manager, '_save_config') as mock_save:
            self.config_manager.reset_config()
            
            # Check that config is reset to defaults
            llm_settings = self.config_manager.get_llm_settings()
            assert llm_settings["model"] == "mistral:7b"  # Default model
            mock_save.assert_called_once()
    
    def test_get_database_connections_empty(self):
        """Test getting database connections when none exist"""
        connections = self.config_manager.get_database_connections()
        assert isinstance(connections, dict)
        assert len(connections) == 0
    
    def test_export_settings_update(self):
        """Test updating export settings"""
        new_settings = {
            "default_format": "xlsx",
            "chart_dpi": 600
        }
        
        with patch.object(self.config_manager, '_save_config') as mock_save:
            self.config_manager.update_export_settings(new_settings)
            
            export_settings = self.config_manager.get_export_settings()
            assert export_settings["default_format"] == "xlsx"
            assert export_settings["chart_dpi"] == 600
            mock_save.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
