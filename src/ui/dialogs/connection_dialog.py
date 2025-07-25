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
            # Use sub_type instead of type for provider selection
            db_sub_type = self.connection_config.get('sub_type', 'mysql')
            
            if db_sub_type == 'mysql':
                success, message = self.test_mysql_connection()
            elif db_sub_type == 'oracle':
                success, message = self.test_oracle_connection()
            elif db_sub_type == 'mongodb':
                success, message = self.test_mongodb_connection()
            elif db_sub_type == 'postgres':
                success, message = self.test_postgres_connection()
            else:
                success, message = False, f"Unsupported database sub-type: {db_sub_type}"
                
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
    
    def test_mongodb_connection(self):
        """Test MongoDB connection"""
        try:
            import pymongo
            
            # Build connection URI
            if self.connection_config.get('username') and self.connection_config.get('password'):
                uri = f"mongodb://{self.connection_config['username']}:{self.connection_config['password']}@{self.connection_config['host']}:{self.connection_config['port']}/{self.connection_config.get('database', 'admin')}"
            else:
                uri = f"mongodb://{self.connection_config['host']}:{self.connection_config['port']}"
            
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=10000)
            # Test connection
            client.admin.command('ping')
            client.close()
            
            return True, "MongoDB connection successful!"
            
        except ImportError:
            return False, "MongoDB driver not installed. Please install pymongo."
        except Exception as e:
            return False, f"MongoDB connection failed: {str(e)}"
    
    def test_postgres_connection(self):
        """Test PostgreSQL connection"""
        try:
            import psycopg2
            
            connection = psycopg2.connect(
                host=self.connection_config['host'],
                port=self.connection_config['port'],
                user=self.connection_config['username'],
                password=self.connection_config['password'],
                database=self.connection_config.get('database', 'postgres'),
                connect_timeout=10
            )
            connection.close()
            
            return True, "PostgreSQL connection successful!"
            
        except ImportError:
            return False, "PostgreSQL driver not installed. Please install psycopg2."
        except Exception as e:
            return False, f"PostgreSQL connection failed: {str(e)}"


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
        
        # Make connection name read-only when editing existing connection
        if self.connection_name:
            self.name_edit.setReadOnly(True)
            self.name_edit.setToolTip("Connection name cannot be changed when editing an existing connection")
            self.name_edit.setStyleSheet("background-color: #f0f0f0;")
        
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Database type and sub-type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Database Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["MySQL", "MongoDB", "PostgreSQL"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        
        # Make database type read-only when editing existing connection
        if self.connection_name:
            self.type_combo.setEnabled(False)
            self.type_combo.setToolTip("Database type cannot be changed when editing an existing connection")
        
        type_layout.addWidget(self.type_combo)
        
        # Add info label for edit mode
        if self.connection_name:
            info_label = QLabel("(Type cannot be changed)")
            info_label.setStyleSheet("color: #666666; font-style: italic; font-size: 10px;")
            type_layout.addWidget(info_label)
        else:
            type_layout.addWidget(QLabel("Type of database to connect to"))
        
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
        elif db_type == "MongoDB":
            self.setup_mongodb_fields()
            self.port_spin.setValue(27017)
        elif db_type == "PostgreSQL":
            self.setup_postgresql_fields()
            self.port_spin.setValue(5432)
    
    def clear_db_specific_fields(self):
        """Clear database-specific fields"""
        # Clear widget references first
        if hasattr(self, 'mysql_schema_edit'):
            delattr(self, 'mysql_schema_edit')
        if hasattr(self, 'oracle_service_edit'):
            delattr(self, 'oracle_service_edit')
        if hasattr(self, 'oracle_conn_type'):
            delattr(self, 'oracle_conn_type')
        if hasattr(self, 'mongo_database_edit'):
            delattr(self, 'mongo_database_edit')
        if hasattr(self, 'mongo_auth_db_edit'):
            delattr(self, 'mongo_auth_db_edit')
        if hasattr(self, 'postgres_database_edit'):
            delattr(self, 'postgres_database_edit')
        if hasattr(self, 'postgres_schema_edit'):
            delattr(self, 'postgres_schema_edit')
        
        # Remove and delete widgets from layout
        while self.db_specific_layout.count() > 0:
            child = self.db_specific_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                widget.setParent(None)
                widget.deleteLater()
    
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
    
    def setup_mongodb_fields(self):
        """Set up MongoDB-specific fields"""
        mongo_group = QGroupBox("MongoDB Settings")
        mongo_layout = QFormLayout(mongo_group)
        
        # Default Database
        self.mongo_database_edit = QLineEdit()
        self.mongo_database_edit.setPlaceholderText("The database to use as default. Leave blank for 'admin'.")
        mongo_layout.addRow("Default Database:", self.mongo_database_edit)
        
        # Authentication Database
        self.mongo_auth_db_edit = QLineEdit()
        self.mongo_auth_db_edit.setPlaceholderText("Database for authentication. Usually 'admin'.")
        mongo_layout.addRow("Auth Database:", self.mongo_auth_db_edit)
        
        self.db_specific_layout.addWidget(mongo_group)
    
    def setup_postgresql_fields(self):
        """Set up PostgreSQL-specific fields"""
        postgres_group = QGroupBox("PostgreSQL Settings")
        postgres_layout = QFormLayout(postgres_group)
        
        # Default Database
        self.postgres_database_edit = QLineEdit()
        self.postgres_database_edit.setPlaceholderText("The database to connect to. Default is 'postgres'.")
        postgres_layout.addRow("Database:", self.postgres_database_edit)
        
        # Schema
        self.postgres_schema_edit = QLineEdit()
        self.postgres_schema_edit.setPlaceholderText("Default schema. Usually 'public'.")
        postgres_layout.addRow("Schema:", self.postgres_schema_edit)
        
        self.db_specific_layout.addWidget(postgres_group)
    
    def get_connection_config(self):
        """Get the current connection configuration with new type/sub-type structure"""
        db_type = self.type_combo.currentText()
        
        # Map UI display names to sub-types
        sub_type_map = {
            "MySQL": "mysql",
            "MongoDB": "mongodb", 
            "PostgreSQL": "postgres"
        }
        
        config = {
            'type': 'DB',  # New connection type
            'sub_type': sub_type_map.get(db_type, 'mysql'),  # New sub-type
            'host': self.hostname_edit.text(),
            'port': self.port_spin.value(),
            'username': self.username_edit.text(),
            'password': self.password_edit.text(),
            'timeout': self.timeout_spin.value(),
            'autocommit': self.autocommit_check.isChecked(),
            'enabled': True  # Default to enabled
        }
        
        # Only access database-specific fields for the current database type
        if db_type == 'MySQL':
            config['database'] = getattr(self, 'mysql_schema_edit', QLineEdit()).text()
        elif db_type == 'Oracle':
            config['service_name'] = getattr(self, 'oracle_service_edit', QLineEdit()).text()
        elif db_type == 'MongoDB':
            config['database'] = getattr(self, 'mongo_database_edit', QLineEdit()).text()
            config['auth_database'] = getattr(self, 'mongo_auth_db_edit', QLineEdit()).text() or 'admin'
        elif db_type == 'PostgreSQL':
            config['database'] = getattr(self, 'postgres_database_edit', QLineEdit()).text() or 'postgres'
            config['schema'] = getattr(self, 'postgres_schema_edit', QLineEdit()).text() or 'public'
        
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
                
                # Map sub-types to UI display names
                sub_type_to_display = {
                    'mysql': 'MySQL',
                    'mongodb': 'MongoDB',
                    'postgres': 'PostgreSQL'
                }
                
                sub_type = config.get('sub_type', 'mysql')
                display_type = sub_type_to_display.get(sub_type, 'MySQL')
                self.type_combo.setCurrentText(display_type)
                
                self.hostname_edit.setText(config.get('host', ''))
                self.port_spin.setValue(config.get('port', 3306))
                self.username_edit.setText(config.get('username', ''))
                # Note: Password is not loaded for security reasons
                
                # Load database-specific fields after the UI has been set up
                if sub_type == 'mysql' and hasattr(self, 'mysql_schema_edit'):
                    self.mysql_schema_edit.setText(config.get('database', ''))
                elif sub_type == 'oracle' and hasattr(self, 'oracle_service_edit'):
                    self.oracle_service_edit.setText(config.get('service_name', ''))
                elif sub_type == 'mongodb':
                    if hasattr(self, 'mongo_database_edit'):
                        self.mongo_database_edit.setText(config.get('database', ''))
                    if hasattr(self, 'mongo_auth_db_edit'):
                        self.mongo_auth_db_edit.setText(config.get('auth_database', 'admin'))
                elif sub_type == 'postgres':
                    if hasattr(self, 'postgres_database_edit'):
                        self.postgres_database_edit.setText(config.get('database', 'postgres'))
                    if hasattr(self, 'postgres_schema_edit'):
                        self.postgres_schema_edit.setText(config.get('schema', 'public'))
                
        except Exception as e:
            self.logger.error(f"Error loading connection config: {e}")
            QMessageBox.warning(
                self,
                "Error Loading Connection",
                f"Failed to load connection configuration:\n{str(e)}"
            )
