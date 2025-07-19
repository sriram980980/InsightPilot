# UI Components

This directory contains the user interface components for InsightPilot.

## Structure

```
ui/
├── __init__.py
├── main_window.py          # Main application window
├── tabs/                   # Tab components
│   ├── __init__.py
│   ├── connections_tab.py  # Database connections management
│   ├── query_chat_tab.py   # Natural language query interface
│   ├── results_tab.py      # Query results and visualizations
│   └── history_tab.py      # Query history and favorites
└── dialogs/                # Dialog components
    ├── __init__.py
    └── connection_dialog.py # Database connection configuration
```

## Features Implemented

### Main Window (`main_window.py`)
- Tabbed interface with proper mode handling (standalone/client)
- Menu system with File > New Connection
- Status bar showing current mode
- Theme support (light/dark)
- Font size configuration

### Connections Tab (`connections_tab.py`)
- Database connection management
- Support for MySQL and Oracle databases
- Connection testing with threaded operations
- Edit/Delete functionality
- Connection status display

### Connection Dialog (`connection_dialog.py`)
- Multi-database support (MySQL, Oracle)
- Tabbed interface (Parameters, SSL, Advanced)
- Real-time connection testing
- Secure password handling
- Validation and error handling
- Database-specific configuration options

### Other Tabs
- **Query Chat Tab**: Natural language query interface (placeholder)
- **Results Tab**: Query results and visualizations (with sample data)
- **History Tab**: Query history and favorites management

## Usage

### Running the Application

```bash
# Standalone mode (default)
python run_insightpilot.py

# Client mode
python run_insightpilot.py --mode client

# Server mode (headless)
python run_insightpilot.py --mode server
```

### Adding Sample Connections

```bash
python add_sample_connections.py
```

### Testing the UI

```bash
python test_ui_manual.py
```

## Database Support

### MySQL
- Host, Port, Username, Password
- Default Schema selection
- Connection testing with mysql-connector-python

### Oracle
- Host, Port, Username, Password
- Service Name or SID
- Connection Type selection (Basic/TNS/Advanced)
- Connection testing with oracledb

## Security Features

- Passwords can be stored in system keyring
- Configuration encryption via ConfigManager
- Connection validation and timeout handling
- Error handling for missing database drivers

## Future Enhancements

1. **MongoDB Support**: Add MongoDB connection dialog and adapter
2. **SSL Configuration**: Implement SSL/TLS settings tab
3. **Connection Pooling**: Add connection pool configuration
4. **Import/Export**: Connection configuration import/export
5. **Connection Groups**: Organize connections by environment/project
6. **Connection History**: Track connection usage statistics
