# 🔧 InsightPilot Troubleshooting Guide

> **Comprehensive solutions for common issues and advanced troubleshooting**

## 🎯 Quick Issue Resolution

### Most Common Issues

| 🚨 Issue | ⚡ Quick Fix | 📖 Details |
|----------|-------------|-------------|
| Cannot connect to database | Check credentials & network | [Database Connection Issues](#database-connection-issues) |
| Query generation fails | Verify LLM service running | [LLM Service Issues](#llm-service-issues) |
| Charts not displaying | Check data format & chart type | [Visualization Issues](#visualization-issues) |
| Slow performance | Limit result size & optimize queries | [Performance Issues](#performance-issues) |
| Installation problems | Check Python version & dependencies | [Installation Issues](#installation-issues) |

---

## 🗄️ Database Connection Issues

### Problem: "Cannot connect to database"

#### Symptoms
- Red connection status indicator
- Error message: "Connection failed" or "Network unreachable"
- Timeout errors during connection attempts

#### Diagnostic Steps

1. **Basic Connectivity Test**
   ```bash
   # Test network connectivity
   ping [database_host]
   
   # Test port accessibility
   telnet [database_host] [port]
   # or
   nc -zv [database_host] [port]
   ```

2. **Database Service Status**
   ```bash
   # MySQL
   sudo systemctl status mysql
   
   # PostgreSQL
   sudo systemctl status postgresql
   
   # Oracle (check listener)
   lsnrctl status
   ```

3. **Firewall and Network**
   ```bash
   # Check if port is open
   sudo netstat -tlnp | grep [port]
   
   # Check firewall rules (Linux)
   sudo ufw status
   
   # Check iptables
   sudo iptables -L
   ```

#### Solutions

##### ✅ **Credential Issues**
```python
# Verify credentials manually
import mysql.connector  # Example for MySQL

try:
    connection = mysql.connector.connect(
        host='your_host',
        port=3306,
        user='your_username',
        password='your_password',
        database='your_database'
    )
    print("✅ Connection successful")
    connection.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

##### ✅ **Network Configuration**
```yaml
# Common port configurations
MySQL: 3306
PostgreSQL: 5432
Oracle: 1521
MongoDB: 27017
SQL Server: 1433
```

##### ✅ **SSL/TLS Issues**
```python
# For databases requiring SSL
connection_params = {
    'ssl_disabled': False,
    'ssl_ca': '/path/to/ca.pem',
    'ssl_cert': '/path/to/client-cert.pem',
    'ssl_key': '/path/to/client-key.pem'
}
```

### Problem: "Authentication failed"

#### Symptoms
- Credentials rejected
- Permission denied errors
- "Access denied for user" messages

#### Solutions

##### ✅ **User Permissions**
```sql
-- MySQL: Grant necessary permissions
GRANT SELECT, SHOW DATABASES ON *.* TO 'username'@'%';
FLUSH PRIVILEGES;

-- Check user permissions
SHOW GRANTS FOR 'username'@'%';
```

##### ✅ **Database User Configuration**
```sql
-- Oracle: Check user status
SELECT username, account_status FROM dba_users WHERE username = 'YOUR_USER';

-- Unlock user if needed
ALTER USER your_user ACCOUNT UNLOCK;
```

### Problem: "Database not accessible"

#### Symptoms
- Database appears to connect but no tables visible
- "No schema information available" error
- Empty database lists

#### Solutions

##### ✅ **Schema Permissions**
```sql
-- MySQL: Check database access
SHOW DATABASES;
USE your_database;
SHOW TABLES;

-- Oracle: Check schema access
SELECT * FROM all_tables WHERE owner = 'SCHEMA_NAME';
```

##### ✅ **Case Sensitivity**
```python
# Some databases are case-sensitive
database_name = "MyDatabase"  # Exact case matters
table_name = "Customer_Data"  # Check actual table names
```

---

## 🤖 LLM Service Issues

### Problem: "LLM generation failed"

#### Symptoms
- "Failed to generate SQL query" errors
- Long timeouts during query generation
- Empty or malformed responses from AI

#### Diagnostic Steps

1. **Check Ollama Service**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Check Ollama logs
   ollama logs
   
   # Restart Ollama if needed
   ollama serve
   ```

2. **Model Availability**
   ```bash
   # List available models
   ollama list
   
   # Pull required model if missing
   ollama pull mistral:7b
   ```

3. **Memory Usage**
   ```bash
   # Check system memory
   free -h
   
   # Check GPU memory (if using GPU)
   nvidia-smi
   ```

#### Solutions

##### ✅ **Ollama Service Issues**
```bash
# Start Ollama service
ollama serve

# Pull the correct model
ollama pull mistral:7b

# Test model directly
ollama run mistral:7b "Hello, can you help me?"
```

##### ✅ **Memory Issues**
```yaml
# Reduce model size or use smaller models
Models by size:
- mistral:7b (4GB RAM)
- llama2:7b (4GB RAM) 
- codellama:7b (4GB RAM)
- tinyllama:1b (1GB RAM)  # For low-memory systems
```

##### ✅ **Network Configuration**
```python
# Configure custom Ollama endpoint
llm_config = {
    "provider": "ollama",
    "base_url": "http://custom-server:11434",
    "timeout": 60,  # Increase timeout
    "model": "mistral:7b"
}
```

### Problem: "Model not responding"

#### Symptoms
- Infinite loading during query generation
- Timeout errors after long waits
- Inconsistent response quality

#### Solutions

##### ✅ **Model Optimization**
```bash
# Use optimized model variants
ollama pull mistral:7b-instruct-q4_0  # Quantized version
ollama pull codellama:7b-code         # Code-optimized
```

##### ✅ **Prompt Optimization**
```python
# Simplify complex questions
Instead of: "Show me a comprehensive analysis of sales performance across all regions with year-over-year comparison"
Try: "Show me sales by region this year vs last year"
```

---

## 📊 Visualization Issues

### Problem: "Charts not displaying"

#### Symptoms
- Blank chart area
- "Failed to generate chart" errors
- Charts showing but with wrong data

#### Diagnostic Steps

1. **Data Format Check**
   ```python
   # Check if data is suitable for charts
   print(f"Columns: {result.columns}")
   print(f"Row count: {result.row_count}")
   print(f"Sample data: {result.rows[:5]}")
   ```

2. **Chart Type Compatibility**
   ```python
   # Verify chart type matches data
   chart_requirements = {
       'bar': 'Categorical + Numeric columns',
       'line': 'Ordered + Numeric columns', 
       'pie': 'Categorical + Numeric (≤10 categories)',
       'scatter': 'Two numeric columns',
       'histogram': 'Single numeric column'
   }
   ```

#### Solutions

##### ✅ **Data Compatibility**
```python
# Ensure proper data types
def check_data_for_chart(result, chart_type):
    if chart_type == 'pie' and len(result.rows) > 10:
        return "Too many categories for pie chart"
    
    if chart_type == 'scatter' and len(result.columns) < 2:
        return "Scatter plot needs 2+ columns"
    
    return "OK"
```

##### ✅ **Chart Generation Debugging**
```python
# Enable debug logging
import logging
logging.getLogger('visualization').setLevel(logging.DEBUG)

# Manual chart generation test
from visualization.chart_renderer import ChartRenderer
renderer = ChartRenderer()
chart_bytes = renderer.render_chart(result, chart_type='bar')
```

### Problem: "Zoom functionality not working"

#### Symptoms
- Mouse wheel doesn't zoom
- Zoom buttons unresponsive
- Chart pixelated when zoomed

#### Solutions

##### ✅ **Enhanced Chart Widget**
```python
# Ensure enhanced chart widget is used
from ui.widgets.enhanced_chart_widget import EnhancedChartArea

# Check if zoom controls are enabled
chart_area = EnhancedChartArea()
chart_area.display_chart(chart_bytes)  # Should enable zoom
```

##### ✅ **Qt/PySide Configuration**
```python
# Check PySide6 installation
pip install --upgrade PySide6

# Verify widget hierarchy
widget_parent = enhanced_chart_area.parent()
print(f"Parent widget: {widget_parent}")
```

---

## ⚡ Performance Issues

### Problem: "Slow query execution"

#### Symptoms
- Queries taking minutes to complete
- UI freezing during query execution
- Memory usage growing continuously

#### Diagnostic Steps

1. **Query Analysis**
   ```sql
   -- Check query execution plan
   EXPLAIN SELECT * FROM large_table WHERE complex_condition;
   
   -- Look for missing indexes
   SHOW INDEX FROM table_name;
   ```

2. **System Resources**
   ```bash
   # Monitor system performance
   top -p $(pgrep python)
   
   # Check memory usage
   ps aux | grep insightpilot
   
   # Check disk I/O
   iotop
   ```

#### Solutions

##### ✅ **Query Optimization**
```python
# Automatic LIMIT clauses
def optimize_query(query):
    if "LIMIT" not in query.upper():
        query += " LIMIT 1000"  # Reasonable default
    return query

# Index recommendations
def suggest_indexes(table_name, where_columns):
    return f"CREATE INDEX idx_{table_name}_{'_'.join(where_columns)} ON {table_name}({', '.join(where_columns)})"
```

##### ✅ **Connection Pooling**
```python
# Configure connection pool
pool_config = {
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 3600
}
```

##### ✅ **Result Set Limitation**
```python
# Smart result limiting
def apply_smart_limits(query, estimated_rows):
    if estimated_rows > 10000:
        # Add sampling for large datasets
        return f"SELECT * FROM ({query}) AS subquery ORDER BY RAND() LIMIT 5000"
    elif estimated_rows > 1000:
        return f"{query} LIMIT 1000"
    return query
```

### Problem: "UI becomes unresponsive"

#### Symptoms
- Interface freezes during operations
- Cannot cancel running queries
- Application needs to be force-closed

#### Solutions

##### ✅ **Threading Configuration**
```python
# Ensure operations run in background threads
from PySide6.QtCore import QThread, Signal

class QueryThread(QThread):
    result_ready = Signal(object)
    
    def run(self):
        # Execute query in background
        result = self.client_api.execute_query(self.request)
        self.result_ready.emit(result)
```

##### ✅ **Progress Feedback**
```python
# Implement proper progress reporting
def execute_with_progress(request, progress_callback):
    progress_callback("Starting query execution!")
    # ... execution logic
    progress_callback("Query completed successfully")
```

---

## 🛠️ Installation Issues

### Problem: "Dependencies not installing"

#### Symptoms
- pip install failures
- Missing module errors
- Version conflicts

#### Solutions

##### ✅ **Python Environment**
```bash
# Check Python version
python --version  # Should be 3.8+

# Create clean virtual environment
python -m venv insightpilot_env
source insightpilot_env/bin/activate  # Linux/Mac
# or
insightpilot_env\Scripts\activate.bat  # Windows

# Upgrade pip
pip install --upgrade pip
```

##### ✅ **Dependency Resolution**
```bash
# Install with verbose output
pip install -r requirements.txt -v

# Install specific problematic packages
pip install PySide6==6.6.0
pip install matplotlib==3.7.0
pip install pandas==2.0.0

# Clear pip cache if needed
pip cache purge
```

##### ✅ **System Dependencies**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev python3-pip build-essential

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel

# macOS (using Homebrew)
brew install python@3.11
```

### Problem: "Ollama installation issues"

#### Symptoms
- Ollama command not found
- Model download failures
- Service startup errors

#### Solutions

##### ✅ **Ollama Installation**
```bash
# Linux/Mac installation
curl -fsSL https://ollama.ai/install.sh | sh

# Windows installation
# Download from https://ollama.ai/download

# Verify installation
ollama --version
```

##### ✅ **Model Management**
```bash
# Pull required models
ollama pull mistral:7b

# Check available space
df -h

# Clean up unused models
ollama rm unused_model_name
```

---

## 🔍 Advanced Debugging

### Logging Configuration

Enable detailed logging to diagnose issues:

```python
# logging_config.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('insightpilot.log'),
        logging.StreamHandler()
    ]
)

# Enable specific component logging
logging.getLogger('api.client_api').setLevel(logging.DEBUG)
logging.getLogger('llm.enhanced_llm_client').setLevel(logging.DEBUG)
logging.getLogger('visualization.chart_renderer').setLevel(logging.DEBUG)
```

### Debug Mode

Run InsightPilot in debug mode for detailed output:

```bash
# Enable debug mode
export INSIGHTPILOT_DEBUG=1
python run_insightpilot.py

# Windows
set INSIGHTPILOT_DEBUG=1
python run_insightpilot.py
```

### Configuration Validation

```python
# Validate configuration
from config.config_manager import ConfigManager

config = ConfigManager()
validation_results = config.validate_configuration()

for component, status in validation_results.items():
    print(f"{component}: {status}")
```

### Memory Profiling

```python
# Profile memory usage
import tracemalloc

tracemalloc.start()

# ... run your operations ...

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
tracemalloc.stop()
```

---

## 🆘 Getting Help

### Before Seeking Help

1. **Check Logs**
   ```bash
   # Check application logs
   tail -f insightpilot.log
   
   # Check system logs
   journalctl -f  # Linux
   # or
   tail -f /var/log/system.log  # macOS
   ```

2. **Gather System Information**
   ```python
   # System info script
   import platform
   import sys
   import PySide6
   
   print(f"OS: {platform.platform()}")
   print(f"Python: {sys.version}")
   print(f"PySide6: {PySide6.__version__}")
   ```

3. **Test Basic Functionality**
   ```python
   # Minimal test script
   from api.client_api import ClientAPI
   from config.config_manager import ConfigManager
   
   try:
       config = ConfigManager()
       api = ClientAPI(config)
       print("✅ Core components initialized successfully")
   except Exception as e:
       print(f"❌ Initialization failed: {e}")
   ```

### Community Resources

- **📖 Documentation**: [GitHub Wiki](https://github.com/username/InsightPilot/wiki)
- **💬 Discussions**: [GitHub Discussions](https://github.com/username/InsightPilot/discussions)
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/username/InsightPilot/issues)
- **💡 Feature Requests**: [GitHub Issues](https://github.com/username/InsightPilot/issues/new?template=feature_request.md)

### Issue Reporting Template

```markdown
## Bug Report

**Environment:**
- OS: [e.g., Windows 11, Ubuntu 22.04]
- Python Version: [e.g., 3.11.5]
- InsightPilot Version: [e.g., 1.0.0]
- Database Type: [e.g., MySQL 8.0]

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Behavior:**
What you expected to happen

**Actual Behavior:**
What actually happened

**Error Messages:**
```
Paste any error messages here
```

**Additional Context:**
Any additional information that might help
```

---

## 📚 Performance Optimization Tips

### Database Optimization

```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_customers_region ON customers(region);

-- Optimize table statistics
ANALYZE TABLE orders;
ANALYZE TABLE customers;

-- Consider partitioning for large tables
ALTER TABLE sales PARTITION BY RANGE (YEAR(sale_date)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025)
);
```

### Application Optimization

```python
# Connection pooling
connection_pool = {
    'pool_size': 5,
    'max_overflow': 10,
    'pool_recycle': 3600
}

# Query result caching
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query_execution(query_hash):
    # Cache frequently used queries
    pass

# Async operations
import asyncio

async def execute_multiple_queries(queries):
    tasks = [execute_query_async(q) for q in queries]
    return await asyncio.gather(*tasks)
```

---

<div align="center">

**🎯 Still Having Issues?**

Don't hesitate to reach out to our community or create a detailed bug report.

[← API Reference](API_REFERENCE.md) | [Performance Guide →](PERFORMANCE.md)

</div>
