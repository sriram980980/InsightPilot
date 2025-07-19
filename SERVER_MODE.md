# InsightPilot Server Mode Documentation

## Overview

InsightPilot now supports running a gRPC server alongside the UI in standalone mode, allowing external clients to connect and use the same AI-powered data exploration capabilities.

## Modes of Operation

### 1. Standalone Mode (Default)
- **Description**: Runs both the UI and gRPC server
- **Use Case**: Single-user desktop application with server capabilities
- **Features**:
  - Full UI interface
  - Background gRPC server on localhost:50051
  - Can accept connections from external clients
  - Local LLM processing
  - Direct database connections

**Command**: 
```bash
python run_insightpilot.py --mode standalone
# or
python src/main.py --mode standalone
```

### 2. Client Mode
- **Description**: UI only, connects to remote gRPC server
- **Use Case**: Thin client connecting to remote InsightPilot server
- **Features**:
  - Full UI interface
  - Connects to remote server for processing
  - No local LLM or database connections

**Command**:
```bash
python run_insightpilot.py --mode client
```

### 3. Server Mode
- **Description**: Headless gRPC server only
- **Use Case**: Dedicated server for multiple clients
- **Features**:
  - No UI (headless)
  - gRPC server with configurable host/port
  - LLM processing and database connections
  - Can serve multiple clients simultaneously

**Command**:
```bash
python run_insightpilot.py --mode server --host 0.0.0.0 --port 50051
```

## Server Configuration

### Default Settings
- **Host**: localhost (standalone), 0.0.0.0 (server mode)
- **Port**: 50051
- **Max Workers**: 10 concurrent connections

### Custom Configuration
```bash
# Custom host and port
python run_insightpilot.py --mode standalone --host 127.0.0.1 --port 8080

# Server mode with specific binding
python run_insightpilot.py --mode server --host 0.0.0.0 --port 50051
```

## Server Features

### 1. Background Server Thread
- Runs in separate QThread to avoid blocking UI
- Graceful startup and shutdown
- Error handling and status reporting

### 2. Server Status Indicators
- Status bar shows server state
- Visual indicators for:
  - Server starting (orange)
  - Server running (green)
  - Server error (red)

### 3. Graceful Shutdown
- Proper cleanup on application exit
- Server thread termination handling
- 5-second timeout for clean shutdown

## Client Integration

### Connecting to InsightPilot Server
External clients can connect to the gRPC server using standard gRPC client libraries:

```python
import grpc
# Example client connection (service definitions to be implemented)
channel = grpc.insecure_channel('localhost:50051')
# Use generated client stubs here
```

### Supported Operations (Future)
- Natural language query processing
- Database schema exploration
- Data visualization requests
- Connection management
- Query history access

## Architecture

```
Standalone Mode:
┌─────────────────┐    ┌─────────────────┐
│   UI (QThread)  │    │ gRPC Server     │
│                 │    │ (QThread)       │
│ - Main Window   │    │ - Client API    │
│ - Tabs          │    │ - LLM Client    │
│ - Dialogs       │    │ - DB Adapters   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                    │
            ┌─────────────────┐
            │ Config Manager  │
            │ & Shared State  │
            └─────────────────┘
```

## Testing

Use the provided test script to verify server functionality:

```bash
python test_server.py
```

This will test:
- Server component initialization
- UI integration
- Configuration loading
- Thread management

## Error Handling

### Common Issues
1. **Port Already in Use**: Change port with `--port` option
2. **Import Errors**: Ensure all dependencies are installed
3. **Configuration Issues**: Check config file path and permissions

### Debugging
Enable debug logging:
```bash
python run_insightpilot.py --mode standalone --log-level DEBUG
```

## Future Enhancements

1. **gRPC Service Definitions**: Complete protobuf definitions for all services
2. **Authentication**: Add user authentication for server connections
3. **Load Balancing**: Support for multiple server instances
4. **Monitoring**: Server health checks and metrics
5. **Configuration UI**: Server settings in the UI
6. **SSL/TLS**: Secure connections support

## Security Considerations

1. **Network Exposure**: Server mode exposes services on network
2. **Authentication**: No authentication in current implementation
3. **Data Access**: Server has full database access permissions
4. **Logging**: Sensitive data may appear in logs

## Performance

- **Concurrent Connections**: Up to 10 simultaneous clients
- **Memory Usage**: Shared resources between UI and server threads
- **Response Time**: Local processing ensures low latency
- **Scalability**: Single-instance design for desktop use

## Troubleshooting

### Server Won't Start
1. Check if port is available
2. Verify gRPC dependencies are installed
3. Check log files for detailed errors

### UI Becomes Unresponsive
1. Server runs in background thread (should not block UI)
2. Check system resources
3. Restart application if needed

### Client Connection Issues
1. Verify server is running and listening
2. Check firewall settings
3. Ensure correct host/port configuration
