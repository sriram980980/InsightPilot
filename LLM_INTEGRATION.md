# LLM Integration Documentation

## Overview

InsightPilot now includes comprehensive LLM (Large Language Model) integration, allowing users to:
- Manage external LLM connections (remote LLM servers)
- Start and control local LLM models via Ollama
- Use both database and LLM connections in a unified interface

## Features Added

### 1. LLM Connection Management
- **New LLM Connection Dialog**: Complete UI for configuring LLM connections
- **Connection Testing**: Test LLM server connectivity and model availability
- **Unified Connection Management**: Database and LLM connections in one interface

### 2. Local LLM Control
- **Start/Stop Local LLM**: Control Ollama server and models directly from UI
- **Model Management**: Download and manage different LLM models
- **Real-time Status**: Live status updates and progress indicators

### 3. Enhanced Connections Tab
- **Dual-Purpose Interface**: Manage both database and LLM connections
- **Connection Filtering**: Filter by connection type (All, Database, LLM)
- **LLM Model Control**: Dedicated controls for local LLM management

## Components

### LLM Connection Dialog (`llm_connection_dialog.py`)
**Purpose**: Configure external LLM server connections

**Features**:
- Server configuration (host, port, model)
- Generation parameters (temperature, max tokens)
- Connection testing with progress indicators
- Model discovery from remote servers

**Usage**:
```python
from ui.dialogs.llm_connection_dialog import LLMConnectionDialog

dialog = LLMConnectionDialog(config_manager)
if dialog.exec() == dialog.Accepted:
    # Connection saved automatically
    pass
```

### LLM Service (`llm_service.py`)
**Purpose**: Manage local LLM model startup and control

**Features**:
- Ollama installation detection
- Background model startup with progress tracking
- Model downloading and management
- Server health monitoring

**Usage**:
```python
from llm.llm_service import LLMService

service = LLMService()
startup_thread = service.start_model("mistral:7b")
startup_thread.startup_progress.connect(progress_handler)
startup_thread.startup_complete.connect(completion_handler)
startup_thread.start()
```

### Enhanced Connections Tab
**Purpose**: Unified interface for all connection types

**New Features**:
- LLM model control section
- Connection type filtering
- Separate buttons for database vs LLM connections
- Integrated testing for both connection types

## Configuration

### LLM Connection Format
```json
{
  "type": "LLM",
  "host": "localhost",
  "port": 11434,
  "model": "mistral:7b",
  "temperature": 0.1,
  "max_tokens": 1000
}
```

### Config Manager Updates
The configuration now supports both database and LLM connections:

```python
# Save LLM connection
config_manager.save_connection("Local Ollama", llm_config)

# Retrieve all connections (database + LLM)
connections = config_manager.get_connections()

# Filter by type
llm_connections = {name: config for name, config in connections.items() 
                   if config.get('type') == 'LLM'}
```

## User Interface

### LLM Model Control Section
Located at the top of the Connections tab:

1. **Status Display**: Shows current LLM status
   - Green: LLM running with model count
   - Orange: LLM stopped but available
   - Red: Ollama not installed

2. **Control Buttons**:
   - **Start Local LLM**: Launches Ollama and pulls default model
   - **Stop LLM**: Stops the local LLM server

3. **Progress Indicators**:
   - Progress bar for startup operations
   - Status messages for detailed feedback

### Connection Management
Enhanced with dual-type support:

1. **Filter Dropdown**: Filter connections by type
   - All: Show all connections
   - Database: Show only database connections
   - LLM: Show only LLM connections

2. **Connection Buttons**:
   - **New Database**: Create database connection
   - **New LLM**: Create LLM connection
   - **Edit/Delete/Test**: Works with both types

3. **Connection Table**: Shows unified view with appropriate columns

## Workflow Examples

### Setting Up Local LLM
1. Click "Start Local LLM" button
2. System checks for Ollama installation
3. If not installed, shows error message
4. If installed, starts Ollama server
5. Downloads default model (mistral:7b) if needed
6. Shows progress and completion status

### Adding External LLM Connection
1. Click "New LLM" button
2. Fill in connection details:
   - Name: "Remote LLM Server"
   - Host: "llm-server.company.com"
   - Port: 11434
   - Model: "gpt-4"
3. Click "Test Connection" to verify
4. Save configuration

### Using LLM Connections
1. Filter connections to show only LLM type
2. Select an LLM connection
3. Click "Test Connection" to verify availability
4. Use in query processing (integration with chat tab)

## Prerequisites

### For Local LLM (Ollama)
1. **Install Ollama**: Download from https://ollama.ai/
2. **Available Models**: Supports any Ollama-compatible model
3. **System Requirements**: Sufficient RAM for chosen model

### For External LLM Connections
1. **Network Access**: Connectivity to remote LLM servers
2. **API Compatibility**: Server must support Ollama-compatible API
3. **Authentication**: Currently supports basic host/port (auth to be added)

## Error Handling

### Common Issues and Solutions

1. **"Ollama not installed"**
   - Install Ollama from official website
   - Ensure it's in system PATH
   - Restart InsightPilot after installation

2. **"Model pull timeout"**
   - Check internet connection
   - Some models are large (>GB) and take time
   - Increase timeout or use smaller models

3. **"LLM server unreachable"**
   - Verify host and port settings
   - Check firewall settings
   - Ensure target server is running

4. **"Connection test failed"**
   - Verify server is running and accessible
   - Check model name exists on server
   - Review server logs for errors

## Integration Points

### With Query Chat Tab
LLM connections can be used for:
- Natural language to SQL conversion
- Query explanation and optimization
- Data analysis and insights

### With gRPC Server
LLM services are available through the gRPC interface for:
- Remote client access
- Distributed processing
- API integration

## Future Enhancements

### Planned Features
1. **Authentication Support**: API keys, OAuth for LLM servers
2. **Model Management UI**: Download, update, delete models
3. **Performance Monitoring**: Response times, token usage
4. **Advanced Configuration**: Custom prompts, fine-tuning
5. **Multi-Model Support**: Use different models for different tasks

### API Integration
1. **OpenAI Compatibility**: Support for OpenAI API format
2. **Custom Endpoints**: Support for various LLM providers
3. **Streaming Responses**: Real-time response streaming
4. **Batch Processing**: Multiple queries in parallel

## Testing

Run the integration test:
```bash
python test_llm_integration.py
```

Expected output:
- ✓ LLM Service: Tests service creation and status
- ✓ Config Manager: Tests connection saving/loading
- ✓ LLM Dialog: Tests UI component creation
- ✓ Connections Tab: Tests integrated interface

## Troubleshooting

### Debug Mode
Enable debug logging for detailed information:
```bash
python run_insightpilot.py --mode standalone --log-level DEBUG
```

### Log Files
Check `insightpilot.log` for detailed error messages and operation logs.

### Manual Testing
1. Start InsightPilot in standalone mode
2. Go to Connections tab
3. Try LLM control buttons
4. Add test LLM connection
5. Test connection functionality

## Security Considerations

### Local LLM
- Local models run on user's machine
- No data leaves the local environment
- Model files stored locally

### Remote LLM Connections
- Connection details stored encrypted
- No automatic data transmission
- User controls when to send queries

### Best Practices
1. Use local LLM for sensitive data
2. Verify remote server security policies
3. Review connection configurations regularly
4. Monitor LLM usage and costs (for paid services)
