"""
Connection Dialog - Database connection configuration
"""

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox,
    QGroupBox, QMessageBox, QCheckBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont


class ConnectionTestThread(QThread):
    """Thread for testing database connections"""
    result_ready = Signal(bool, str)
    
    def __init__(self, connection_config):
        super().__init__()
        self.connection_config = connection_config
        
    def run(self):
        """Test the database connection"""
        try:
            db_type = self.connection_config['type']
            
            if db_type == 'MySQL':
                success, message = self.test_mysql_connection()
            elif db_type == 'Oracle':
                success, message = self.test_oracle_connection()
            else:
                success, message = False, f"Unsupported database type: {db_type}"
                
            self.result_ready.emit(success, message)
            
        except Exception as e:
            self.result_ready.emit(False, f"Connection test error: {str(e)}")
    
    def test_mysql_connection(self):
        """Test MySQL connection"""
        try:
            import mysql.connector
            
            config = {
                'host': self.connection_config['host'],
                'port': self.connection_config['port'],
                'user': self.connection_config['username'],
                'password': self.connection_config['password'],
                'database': self.connection_config.get('database', ''),
                'connection_timeout': 10
            }
            
            # Remove empty database name
            if not config['database']:
                del config['database']
            
            connection = mysql.connector.connect(**config)
            connection.close()
            
            return True, "MySQL connection successful!"
            
        except ImportError:
            return False, "MySQL connector not installed. Please install mysql-connector-python."
        except Exception as e:
            return False, f"MySQL connection failed: {str(e)}"
    
    def test_oracle_connection(self):
        """Test Oracle connection"""
        try:
            import oracledb
            
            # Build connection string
            if self.connection_config.get('service_name'):
                dsn = f"{self.connection_config['host']}:{self.connection_config['port']}/{self.connection_config['service_name']}"
            else:
                dsn = f"{self.connection_config['host']}:{self.connection_config['port']}/{self.connection_config.get('sid', 'XE')}"
            
            connection = oracledb.connect(
                user=self.connection_config['username'],
                password=self.connection_config['password'],
                dsn=dsn
            )
            connection.close()
            
            return True, "Oracle connection successful!"
            
        except ImportError:
            return False, "Oracle client not installed. Please install oracledb."
        except Exception as e:
            return False, f"Oracle connection failed: {str(e)}"


class ConnectionDialog(QDialog):
    """Dialog for creating/editing database connections"""
    
    def __init__(self, config_manager, connection_name=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.connection_name = connection_name
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle("Setup New Connection" if not connection_name else f"Edit Connection: {connection_name}")
        self.setModal(True)
        self.resize(500, 600)
        
        self.test_thread = None
        
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
        self.name_edit.setPlaceholderText("Type a name for the connection")
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Database type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Connection Method:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["MySQL", "Oracle"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)
        type_layout.addWidget(QLabel("Method to use to connect to the RDBMS"))
        layout.addLayout(type_layout)
        
        # Create tab widget for different parameter sets
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Parameters tab
        self.setup_parameters_tab()
        
        # SSL tab (placeholder)
        self.setup_ssl_tab()
        
        # Advanced tab
        self.setup_advanced_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.test_btn = QPushButton("Test Connection")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn = QPushButton("OK")
        
        self.test_btn.clicked.connect(self.test_connection)
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn.clicked.connect(self.accept_connection)
        
        button_layout.addWidget(self.test_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
        # Initialize with MySQL parameters
        self.on_type_changed("MySQL")
    
    def setup_parameters_tab(self):
        """Set up the parameters tab"""
        params_widget = QWidget()
        self.tab_widget.addTab(params_widget, "Parameters")
        
        layout = QVBoxLayout(params_widget)
        
        # Connection details form
        form_layout = QFormLayout()
        
        # Hostname
        self.hostname_edit = QLineEdit("127.0.0.1")
        form_layout.addRow("Hostname:", self.hostname_edit)
        
        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(3306)  # Default MySQL port
        form_layout.addRow("Port:", self.port_spin)
        
        # Username
        self.username_edit = QLineEdit("root")
        form_layout.addRow("Username:", self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_edit)
        
        # Store in vault checkbox
        self.store_vault_check = QCheckBox("Store in Vault !")
        self.store_vault_check.setChecked(True)
        form_layout.addRow("", self.store_vault_check)
        
        # Clear button for password
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.password_edit.clear())
        form_layout.addRow("", clear_btn)
        
        layout.addLayout(form_layout)
        
        # Database-specific fields (will be added dynamically)
        self.db_specific_layout = QVBoxLayout()
        layout.addLayout(self.db_specific_layout)
        
        layout.addStretch()
    
    def setup_ssl_tab(self):
        """Set up the SSL tab"""
        ssl_widget = QWidget()
        self.tab_widget.addTab(ssl_widget, "SSL")
        
        layout = QVBoxLayout(ssl_widget)
        
        ssl_label = QLabel("SSL Configuration")
        ssl_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(ssl_label)
        
        placeholder_label = QLabel("SSL configuration options will be implemented in the full version.")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(placeholder_label)
        
        layout.addStretch()
    
    def setup_advanced_tab(self):
        """Set up the advanced tab"""
        advanced_widget = QWidget()
        self.tab_widget.addTab(advanced_widget, "Advanced")
        
        layout = QVBoxLayout(advanced_widget)
        
        advanced_label = QLabel("Advanced Options")
        advanced_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(advanced_label)
        
        form_layout = QFormLayout()
        
        # Connection timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        form_layout.addRow("Connection Timeout:", self.timeout_spin)
        
        # Auto-commit
        self.autocommit_check = QCheckBox("Enable auto-commit")
        self.autocommit_check.setChecked(True)
        form_layout.addRow("", self.autocommit_check)
        
        layout.addLayout(form_layout)
        layout.addStretch()
    
    def on_type_changed(self, db_type):
        """Handle database type change"""
        # Clear existing database-specific fields
        self.clear_db_specific_fields()
        
        if db_type == "MySQL":
            self.setup_mysql_fields()
            self.port_spin.setValue(3306)
        elif db_type == "Oracle":
            self.setup_oracle_fields()
            self.port_spin.setValue(1521)
    
    def clear_db_specific_fields(self):
        """Clear database-specific fields"""
        while self.db_specific_layout.count():
            child = self.db_specific_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def setup_mysql_fields(self):
        """Set up MySQL-specific fields"""
        mysql_group = QGroupBox("MySQL Settings")
        mysql_layout = QFormLayout(mysql_group)
        
        # Default Schema
        self.mysql_schema_edit = QLineEdit()
        self.mysql_schema_edit.setPlaceholderText("The schema to use as default schema. Leave blank to select it later.")
        mysql_layout.addRow("Default Schema:", self.mysql_schema_edit)
        
        self.db_specific_layout.addWidget(mysql_group)
    
    def setup_oracle_fields(self):
        """Set up Oracle-specific fields"""
        oracle_group = QGroupBox("Oracle Settings")
        oracle_layout = QFormLayout(oracle_group)
        
        # Connection Type
        self.oracle_conn_type = QComboBox()
        self.oracle_conn_type.addItems(["Basic", "TNS", "Advanced"])
        self.oracle_conn_type.currentTextChanged.connect(self.on_oracle_conn_type_changed)
        oracle_layout.addRow("Connection Type:", self.oracle_conn_type)
        
        # Service Name / SID
        self.oracle_service_edit = QLineEdit()
        self.oracle_service_edit.setPlaceholderText("e.g., orcl.db.oracle.com")
        oracle_layout.addRow("Service name:", self.oracle_service_edit)
        
        self.db_specific_layout.addWidget(oracle_group)
    
    def on_oracle_conn_type_changed(self, conn_type):
        """Handle Oracle connection type change"""
        # This would be implemented for different Oracle connection methods
        pass
    
    def get_connection_config(self):
        """Get the current connection configuration"""
        config = {
            'type': self.type_combo.currentText(),
            'host': self.hostname_edit.text(),
            'port': self.port_spin.value(),
            'username': self.username_edit.text(),
            'password': self.password_edit.text(),
            'timeout': self.timeout_spin.value(),
            'autocommit': self.autocommit_check.isChecked()
        }
        
        if config['type'] == 'MySQL':
            config['database'] = self.mysql_schema_edit.text()
        elif config['type'] == 'Oracle':
            config['service_name'] = self.oracle_service_edit.text()
        
        return config
    
    def test_connection(self):
        """Test the database connection"""
        if not self.validate_inputs():
            return
        
        config = self.get_connection_config()
        
        # Disable test button during test
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing!")
        
        # Start connection test in separate thread
        self.test_thread = ConnectionTestThread(config)
        self.test_thread.result_ready.connect(self.on_test_result)
        self.test_thread.start()
    
    def on_test_result(self, success, message):
        """Handle connection test result"""
        # Re-enable test button
        self.test_btn.setEnabled(True)
        self.test_btn.setText("Test Connection")
        
        if success:
            QMessageBox.information(self, "Connection Test", message)
        else:
            QMessageBox.warning(self, "Connection Test Failed", message)
    
    def validate_inputs(self):
        """Validate user inputs"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a connection name.")
            return False
        
        if not self.hostname_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a hostname.")
            return False
        
        if not self.username_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a username.")
            return False
        
        return True
    
    def accept_connection(self):
        """Accept and save the connection"""
        if not self.validate_inputs():
            return
        
        connection_name = self.name_edit.text().strip()
        config = self.get_connection_config()
        
        try:
            # Save connection to config manager
            self.config_manager.save_connection(connection_name, config)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Connection",
                f"Failed to save connection configuration:\n{str(e)}"
            )
    
    def load_connection_config(self):
        """Load existing connection configuration"""
        if not self.connection_name:
            return
        
        try:
            connections = self.config_manager.get_connections()
            if self.connection_name in connections:
                config = connections[self.connection_name]
                
                self.name_edit.setText(self.connection_name)
                self.type_combo.setCurrentText(config.get('type', 'MySQL'))
                self.hostname_edit.setText(config.get('host', ''))
                self.port_spin.setValue(config.get('port', 3306))
                self.username_edit.setText(config.get('username', ''))
                # Note: Password is not loaded for security reasons
                
                if config['type'] == 'MySQL':
                    self.mysql_schema_edit.setText(config.get('database', ''))
                elif config['type'] == 'Oracle':
                    self.oracle_service_edit.setText(config.get('service_name', ''))
                
        except Exception as e:
            self.logger.error(f"Error loading connection config: {e}")
            QMessageBox.warning(
                self,
                "Error Loading Connection",
                f"Failed to load connection configuration:\n{str(e)}"
            )
