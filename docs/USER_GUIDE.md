# 📖 InsightPilot User Guide

> **Complete guide to using InsightPilot's AI-powered data exploration features**

## 🎯 Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Database Connections](#database-connections)
4. [Natural Language Queries](#natural-language-queries)
5. [Data Visualization](#data-visualization)
6. [Chart Zoom & Interaction](#chart-zoom--interaction)
7. [Exporting Data](#exporting-data)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)

---

## 🚀 Getting Started

### First Launch

1. **Start InsightPilot**
   ```bash
   python run_insightpilot.py
   ```

2. **Initial Setup**
   - The main window opens with four tabs: Connections, Query Chat, Results, History
   - No database connections are configured initially
   - The LLM engine starts automatically in standalone mode

### Quick Tour of the Interface

The InsightPilot interface is organized into logical sections:

- **🔗 Connections Tab**: Manage database connections
- **💬 Query Chat Tab**: Ask questions in natural language  
- **📊 Results Tab**: View and interact with query results
- **📚 History Tab**: Browse past queries and favorites

---

## 🖥️ Interface Overview

### Main Window Components

#### Header Area
- **Menu Bar**: File, Tools, Help menus
- **Status Bar**: Connection status and system messages
- **Progress Indicators**: Real-time feedback during operations

#### Tab Navigation
Each tab serves a specific purpose in your data exploration workflow:

```mermaid
graph LR
    A[Connections] --> B[Query Chat]
    B --> C[Results]
    C --> D[History]
    D --> B
```

---

## 🗄️ Database Connections

### Adding a New Connection

1. **Navigate to Connections Tab**
   - Click the "Connections" tab in the main window

2. **Create New Connection**
   - Click "New Connection" button
   - Fill in the connection details
   - Test the connection
   - Save when successful

### Connection Types

#### MySQL Database
- **Host**: Server address (e.g., localhost, 192.168.1.100)
- **Port**: Usually 3306
- **Database**: Database name
- **Username/Password**: Your credentials

#### Oracle Database  
- **Host**: Oracle server address
- **Port**: Usually 1521
- **Service Name**: Oracle service identifier
- **Username/Password**: Oracle credentials

#### MongoDB
- **Host**: MongoDB server address
- **Port**: Usually 27017
- **Database**: MongoDB database name
- **Username/Password**: MongoDB credentials (if auth enabled)

### Connection Management

#### Testing Connections
- Use the "Test Connection" button to verify settings
- Green checkmark indicates successful connection
- Red X shows connection errors with details

#### Editing Connections
- Select existing connection and click "Edit"
- Modify any settings and test again
- Changes are saved automatically

#### Removing Connections
- Select connection and click "Delete"
- Confirm removal (this cannot be undone)

---

## 💬 Natural Language Queries

### How It Works

InsightPilot uses advanced AI to convert your natural language questions into precise SQL queries:

1. **You ask a question** in plain English
2. **AI analyzes** your database schema
3. **SQL is generated** automatically
4. **Query is validated** for safety
5. **Results are displayed** with visualizations

### Query Examples

#### Sales & Revenue Analysis
```text
"Show me total sales by month for this year"
"Which products have the highest revenue?"
"Compare sales performance between regions"
"Show customers who spent more than $1000"
```

#### Customer Analytics
```text
"How many new customers joined last quarter?"
"Show customer distribution by city"
"Which customers haven't ordered in 6 months?"
"Find the top 10 customers by total purchases"
```

#### Inventory & Products
```text
"Show products that are out of stock"
"Which categories have the most items?"
"List products with low inventory levels"
"Show average product ratings by category"
```

#### Operational Insights
```text
"Show order status distribution"
"How many orders were shipped last week?"
"Compare this month's performance to last month"
"Show daily order trends for the past 30 days"
```

### Query Tips

#### Be Specific
- ✅ "Show sales for electronics category in Q4 2024"
- ❌ "Show some sales data"

#### Use Time Ranges
- ✅ "customers who joined in the last 30 days"
- ✅ "orders placed between January and March"
- ✅ "sales trends for the past year"

#### Specify Aggregations
- ✅ "total revenue by product category"
- ✅ "average order value per customer"
- ✅ "count of orders by status"

#### Include Filters
- ✅ "products with rating above 4 stars"
- ✅ "customers from California and Texas"
- ✅ "orders with value greater than $500"

---

## 📊 Data Visualization

### Automatic Chart Generation

InsightPilot intelligently chooses the best visualization for your data:

#### Chart Type Selection Logic

| Data Pattern | Recommended Chart |
|--------------|-------------------|
| Categories + Numbers | Bar Chart |
| Time Series | Line Chart |
| Parts of Whole | Pie Chart |
| Two Numeric Variables | Scatter Plot |
| Single Numeric Column | Histogram |
| Complex Data | Table View |

### Manual Chart Selection

#### Available Chart Types

1. **📊 Bar Charts**
   - Best for: Comparing categories
   - Example: Sales by product, customers by region

2. **📈 Line Charts**
   - Best for: Trends over time
   - Example: Revenue trends, user growth

3. **🥧 Pie Charts**
   - Best for: Parts of a whole (≤10 categories)
   - Example: Market share, order status distribution

4. **📉 Scatter Plots**
   - Best for: Relationships between variables
   - Example: Price vs. sales, age vs. income

5. **📋 Histograms**
   - Best for: Distribution of values
   - Example: Order values, customer ages

6. **📋 Data Tables**
   - Best for: Raw data inspection
   - Features: Sorting, filtering, searching

### AI Chart Recommendations

#### Using Auto-Recommend
1. **Load your data** by running a query
2. **Click "🤖 Auto Recommend Chart"**
3. **AI analyzes** your data patterns
4. **Chart is generated** with explanation

#### Using Chart Hints
1. **Enter a hint** like "show as pie chart" or "group by month"
2. **Click "💡 Apply Chart Hint"**
3. **AI interprets** your preference
4. **Custom chart** is created

### Chart Customization

#### Visual Enhancements
- **Color Schemes**: Professional color palettes
- **Labels**: Clear axis labels and titles
- **Legends**: Automatic legend placement
- **Grid Lines**: Subtle grid for easy reading

---

## 🔍 Chart Zoom & Interaction

### Enhanced Chart Viewer

The new enhanced chart viewer provides powerful interaction capabilities:

#### Zoom Controls

1. **Mouse Wheel Zoom**
   - Hold `Ctrl` + scroll wheel to zoom in/out
   - Smooth, responsive zooming
   - Centers on mouse cursor position

2. **Toolbar Controls**
   - **🔍+ Zoom In**: Increase zoom by 10%
   - **🔍- Zoom Out**: Decrease zoom by 10%
   - **⊡ Fit to View**: Fit chart to window size
   - **1:1 Reset**: Return to 100% zoom

3. **Zoom Slider**
   - Drag slider for precise zoom control
   - Range: 10% to 500%
   - Real-time zoom percentage display

#### Pan Functionality
- **Click & Drag**: Pan around zoomed charts
- **Smooth Movement**: Fluid panning experience
- **Auto Scroll Bars**: Appear when needed

#### Zoom Features

##### Smart Zoom Limits
- **Minimum**: 10% (overview mode)
- **Maximum**: 500% (detail inspection)
- **Optimal Range**: 50% - 200% for most use cases

##### High-Quality Rendering
- **Vector Graphics**: Crisp at any zoom level
- **Anti-aliasing**: Smooth lines and text
- **Dynamic Resolution**: Adapts to zoom level

### Interaction Examples

#### Exploring Detailed Data
```text
1. Generate a scatter plot of sales vs. profit
2. Zoom in to 200% to examine outliers
3. Pan to different regions of the chart
4. Reset zoom to see overall pattern
```

#### Chart Analysis Workflow
```text
1. Start with auto-recommended chart
2. Use fit-to-view for full overview
3. Zoom into areas of interest
4. Save high-resolution chart image
```

---

## 💾 Exporting Data

### Data Export Options

#### CSV Export
1. **Click "💾 Export Data"** in Results tab
2. **Choose CSV format** in save dialog
3. **Select location** and filename
4. **Data is exported** with headers

**Best for**: Excel analysis, data sharing, backup

#### Excel Export  
1. **Click "💾 Export Data"** in Results tab
2. **Choose Excel format** (.xlsx)
3. **Select location** and filename
4. **Formatted spreadsheet** is created

**Best for**: Business reports, presentations, advanced analysis

### Chart Export Options

#### Image Formats
1. **Click "📸 Save Chart"** in Results tab
2. **Choose format**: PNG, JPEG, PDF
3. **High-resolution export** (300 DPI)
4. **Perfect for presentations**

#### Export Specifications
- **PNG**: Best for web, documentation
- **JPEG**: Smaller files, good for sharing
- **PDF**: Vector format, scalable, print-ready

### Batch Operations

#### Export Multiple Results
1. **Use History tab** to select multiple queries
2. **Bulk export option** (coming soon)
3. **Automated report generation**

---

## 🚀 Advanced Features

### Query History Management

#### Automatic History
- **Every query is saved** automatically
- **Full context preserved**: Question, SQL, results
- **Search functionality**: Find past queries instantly
- **Performance metrics**: Execution time, row count

#### Favorites System
1. **Star important queries** in History tab
2. **Quick access** to frequently used queries
3. **Organize by project** or topic
4. **Export favorite collections**

#### History Search
```text
Search examples:
- "sales" - Find all queries about sales
- "last month" - Queries with time filters
- "customers" - Customer-related queries
```

### LLM Configuration

#### Provider Options
1. **Local Ollama** (Default)
   - Runs on your machine
   - Complete privacy
   - No internet required

2. **External APIs**
   - OpenAI GPT models
   - Custom enterprise LLMs
   - Cloud-based solutions

#### Model Selection
- **Mistral 7B**: Fast, accurate, good for most use cases
- **Llama 2**: Alternative open-source option
- **GPT-4**: Premium option for complex queries

### Performance Optimization

#### Query Optimization
- **Automatic LIMIT clauses**: Prevent huge result sets
- **Index recommendations**: AI suggests database improvements
- **Query caching**: Faster repeated queries

#### Connection Pooling
- **Persistent connections**: Faster query execution
- **Connection limits**: Prevent database overload
- **Timeout management**: Handle slow queries gracefully

---

## 🔧 Troubleshooting

### Common Issues

#### Connection Problems

**Issue**: "Cannot connect to database"
**Solutions**:
- ✅ Verify host and port settings
- ✅ Check network connectivity
- ✅ Confirm database is running
- ✅ Validate username/password
- ✅ Check firewall settings

**Issue**: "Authentication failed"
**Solutions**:
- ✅ Verify credentials
- ✅ Check user permissions
- ✅ Confirm database access rights
- ✅ Try connecting with database client

#### Query Issues

**Issue**: "Query generation failed"
**Solutions**:
- ✅ Rephrase your question more clearly
- ✅ Check if LLM service is running
- ✅ Verify database schema is accessible
- ✅ Try simpler questions first

**Issue**: "No data returned"
**Solutions**:
- ✅ Check if tables contain data
- ✅ Verify table permissions
- ✅ Try broader search criteria
- ✅ Check date ranges and filters

#### Performance Issues

**Issue**: "Slow query execution"
**Solutions**:
- ✅ Add database indexes
- ✅ Limit result set size
- ✅ Optimize database configuration
- ✅ Check database server resources

**Issue**: "Chart rendering slow"
**Solutions**:
- ✅ Reduce data point count
- ✅ Use data sampling
- ✅ Increase system memory
- ✅ Close unnecessary applications

### Getting Help

#### Built-in Resources
- **📖 Help Menu**: Quick reference guides
- **💡 Tooltips**: Hover for contextual help
- **🔍 Status Messages**: Real-time feedback

#### Community Support
- **GitHub Issues**: Bug reports and feature requests
- **Discussion Forums**: Community Q&A
- **Documentation**: Comprehensive guides

#### Diagnostic Information
```text
Help > System Information provides:
- Version details
- System specifications  
- Configuration settings
- Log file locations
```

---

## 📚 Best Practices

### Query Writing Tips

#### Start Simple
1. **Begin with basic questions**
2. **Add complexity gradually**
3. **Test each component**
4. **Build on successful queries**

#### Use Natural Language
- ✅ "Show me" instead of "SELECT"
- ✅ "customers who" instead of "WHERE"
- ✅ "last month" instead of date ranges
- ✅ "total sales" instead of "SUM()"

#### Be Specific with Time
- ✅ "sales in Q4 2024"
- ✅ "orders from last 30 days"
- ✅ "customers who joined this year"

### Data Exploration Workflow

#### Recommended Process
1. **🔍 Explore Schema**: Understand your data structure
2. **❓ Ask Questions**: Start with broad questions
3. **📊 Visualize Results**: Use appropriate chart types
4. **🔎 Drill Down**: Zoom into interesting patterns
5. **💾 Save Insights**: Export important findings
6. **📝 Document**: Keep notes on discoveries

#### Progressive Analysis
```text
Level 1: "Show me total sales"
Level 2: "Show me sales by month"  
Level 3: "Show me sales by month for each product category"
Level 4: "Compare this year's monthly sales to last year by category"
```

---

## 🎓 Learning Resources

### Video Tutorials
- **Getting Started** (5 min): Basic setup and first query
- **Advanced Queries** (10 min): Complex analysis techniques
- **Visualization Guide** (8 min): Chart types and customization
- **Export & Sharing** (6 min): Saving and sharing results

### Sample Datasets
- **Retail Sales**: E-commerce transaction data
- **HR Analytics**: Employee and performance data
- **Financial Data**: Revenue and expense tracking
- **Customer CRM**: Customer relationship data

### Interactive Examples
Try these queries with the sample data:

1. **Sales Analysis**
   ```text
   "Show me the top 10 products by revenue"
   "Compare sales between different regions"
   "What's the trend of sales over the last 12 months?"
   ```

2. **Customer Insights**
   ```text
   "Which customers haven't placed orders recently?"
   "Show customer distribution by age group"
   "Find customers with the highest lifetime value"
   ```

3. **Operational Metrics**
   ```text
   "How many orders are currently pending?"
   "Show average order processing time by month"
   "Which shipping methods are most popular?"
   ```

---

<div align="center">

**🎉 Congratulations!**

You're now ready to explore your data with InsightPilot's powerful AI-driven interface.

[← Back to README](README_NEW.md) | [API Reference →](API_REFERENCE.md)

</div>
