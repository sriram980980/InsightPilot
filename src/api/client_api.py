"""
Client API for UI-to-LLM/DB communication
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from adapters.base_adapter import BaseDBAdapter, QueryResult, TableSchema, DBConnection
from adapters.mysql_adapter import MySQLAdapter
from adapters.oracle_adapter import OracleAdapter
from adapters.mongo_adapter import MongoAdapter
from llm.llm_client import create_llm_client, LLMResponse
from llm.prompt_builder import PromptBuilder
from history.history_manager import HistoryManager, QueryHistoryEntry
from config.config_manager import ConfigManager


@dataclass
class QueryRequest:
    """Query request structure"""
    database_name: str
    question: str
    database_type: str = "mysql"  # mysql, oracle, mongodb
    llm_provider: Optional[str] = None  # LLM provider name to use for this query


@dataclass
class QueryResponse:
    """Query response structure"""
    success: bool
    sql_query: str
    result: Optional[QueryResult]
    explanation: str
    error: Optional[str] = None
    execution_time: float = 0.0


class ClientAPI:
    """Client API for handling UI requests"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize components with enhanced LLM client
        self.llm_client = self._init_llm_client()
        self.prompt_builder = PromptBuilder()
        self.history_manager = HistoryManager()
        
        # Active database adapters
        self.adapters: Dict[str, BaseDBAdapter] = {}
    
    def _init_llm_client(self):
        """Initialize enhanced LLM client from configuration"""
        try:
            # Try to create enhanced LLM client with multiple providers
            return create_llm_client(self.config_manager, legacy_mode=False)
        except Exception as e:
            self.logger.warning(f"Failed to initialize enhanced LLM client, falling back to legacy: {e}")
            # Fallback to legacy Ollama-only client
            return create_llm_client(None, legacy_mode=True)
    
    def get_database_connections(self) -> Dict[str, Any]:
        """Get available database connections"""
        connections = {}
        all_connections = self.config_manager.get_connections()
        
        for name, conn in all_connections.items():
            if conn.get('type') == 'DB':
                # Use sub_type if available, otherwise detect from port
                db_type = conn.get("sub_type", self._detect_db_type(conn.get("port", 3306)))
                
                connections[name] = {
                    "host": conn.get("host", ""),
                    "port": conn.get("port", 3306),
                    "database": conn.get("database", ""),
                    "type": db_type
                }
        return connections
    
    def _detect_db_type(self, port: int) -> str:
        """Detect database type from port (fallback method)"""
        if port == 3306:
            return "mysql"
        elif port == 1521:
            return "oracle"
        elif port == 27017:
            return "mongodb"
        elif port == 5432:
            return "postgres"
        else:
            return "unknown"
    
    def connect_to_database(self, database_name: str) -> bool:
        """Connect to a specific database using sub_type"""
        try:
            all_connections = self.config_manager.get_connections()
            
            if database_name not in all_connections:
                self.logger.error(f"Database connection not found: {database_name}")
                return False
            
            connection = all_connections[database_name]
            
            # Ensure it's a DB connection
            if connection.get('type') != 'DB':
                self.logger.error(f"Connection '{database_name}' is not a database connection")
                return False
            
            # Use sub_type if available, otherwise fallback to port detection
            db_type = connection.get("sub_type", self._detect_db_type(connection.get("port", 3306)))
            
            # Create DBConnection object for adapters
            from adapters.base_adapter import DBConnection
            db_connection = DBConnection(
                host=connection.get("host", "localhost"),
                port=connection.get("port", 3306),
                database=connection.get("database", ""),
                username=connection.get("username", ""),
                password=connection.get("password", ""),
                connection_params=connection.get("connection_params")
            )
            
            # Create appropriate adapter based on sub_type
            if db_type == "mysql":
                adapter = MySQLAdapter(db_connection)
            elif db_type == "oracle":
                adapter = OracleAdapter(db_connection)
            elif db_type == "mongodb":
                adapter = MongoAdapter(db_connection)
            elif db_type == "postgres":
                # Note: PostgreSQLAdapter needs to be implemented
                self.logger.error(f"PostgreSQL adapter not yet implemented for {database_name}")
                return False
            else:
                self.logger.error(f"Unsupported database type '{db_type}' for {database_name}")
                return False
            
            # Test connection
            if adapter.connect():
                self.adapters[database_name] = adapter
                self.logger.info(f"Connected to database: {database_name} (type: {db_type})")
                return True
            else:
                self.logger.error(f"Failed to connect to database: {database_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to database {database_name}: {e}")
            return False
    
    def disconnect_from_database(self, database_name: str) -> bool:
        """Disconnect from a specific database"""
        try:
            if database_name in self.adapters:
                self.adapters[database_name].disconnect()
                del self.adapters[database_name]
                self.logger.info(f"Disconnected from database: {database_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error disconnecting from database {database_name}: {e}")
            return False
    
    def get_database_schema(self, database_name: str) -> List[TableSchema]:
        """Get schema information for a database"""
        if database_name not in self.adapters:
            raise ValueError(f"Not connected to database: {database_name}")
        
        return self.adapters[database_name].get_schema()
    
    def get_schema(self, database_name: str, database_type: str = None) -> Dict[str, Dict]:
        """Get database schema in dictionary format"""
        try:
            if database_name not in self.adapters:
                if not self.connect_to_database(database_name):
                    raise ValueError(f"Could not connect to database: {database_name}")
            
            adapter = self.adapters[database_name]
            schema = adapter.get_schema()
            
            # Convert TableSchema list to dictionary format
            schema_dict = {}
            for table in schema:
                schema_dict[table.name] = {
                    col['name']: {
                        'type': col['type'],
                        'nullable': col.get('nullable', True)
                    } for col in table.columns
                }
            
            return schema_dict
            
        except Exception as e:
            self.logger.error(f"Error getting schema for {database_name}: {e}")
            raise
    
    def _resolve_llm_provider_name(self, llm_connection_name: str) -> str:
        """Resolve LLM connection name to actual provider name using sub_type"""
        if not llm_connection_name:
            return None
            
        try:
            # Get LLM connections from config
            llm_connections = self.config_manager.get_llm_connections()
            
            if llm_connection_name not in llm_connections:
                self.logger.warning(f"LLM connection '{llm_connection_name}' not found in configuration")
                return None
            
            connection = llm_connections[llm_connection_name]
            
            # Check if connection is enabled
            if not connection.get("enabled", True):
                self.logger.warning(f"LLM connection '{llm_connection_name}' is disabled")
                return None
            
            # Verify connection type and sub_type
            if connection.get("type", "").upper() != "LLM":
                self.logger.warning(f"Connection '{llm_connection_name}' is not an LLM connection")
                return None
            
            sub_type = connection.get("sub_type", "").lower()
            if not sub_type:
                self.logger.warning(f"LLM connection '{llm_connection_name}' missing sub_type")
                return None
            
            # Validate sub_type
            valid_subtypes = ["openai", "github", "ollama"]
            if sub_type not in valid_subtypes:
                self.logger.error(f"Invalid LLM sub_type '{sub_type}' for connection '{llm_connection_name}'. Must be one of: {valid_subtypes}")
                return None
            
            # Check if provider exists in enhanced client
            if hasattr(self.llm_client, 'providers') and llm_connection_name in self.llm_client.providers:
                self.logger.info(f"LLM connection '{llm_connection_name}' (sub_type: {sub_type}) found in providers")
                return llm_connection_name
            else:
                self.logger.warning(f"LLM connection '{llm_connection_name}' not found in enhanced client providers {self.llm_client.providers}")
                if hasattr(self.llm_client, 'providers'):
                    available_providers = list(self.llm_client.providers.keys())
                    self.logger.info(f"Available providers: {available_providers}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error resolving LLM connection '{llm_connection_name}': {e}")
            return None
    
    def execute_natural_language_query(self, request: QueryRequest) -> QueryResponse:
        """Execute a natural language query"""
        return self.execute_natural_language_query_with_progress(request)
    
    def execute_natural_language_query_with_progress(self, request: QueryRequest, progress_callback=None, table_callback=None) -> QueryResponse:
        """Execute a natural language query with progress reporting"""
        import time
        start_time = time.time()
        
        def report_progress(message):
            if progress_callback:
                progress_callback(message)
            self.logger.info(message)
        
        def report_table(table_name):
            if table_callback:
                table_callback(table_name)
        
        try:
            report_progress("Establishing database connection!")
            
            # Check if connected to database
            if request.database_name not in self.adapters:
                if not self.connect_to_database(request.database_name):
                    return QueryResponse(
                        success=False,
                        sql_query="",
                        result=None,
                        explanation="",
                        error=f"Could not connect to database: {request.database_name}. Please check your database connection settings.",
                        execution_time=time.time() - start_time
                    )
            
            adapter = self.adapters[request.database_name]
            report_progress("Connected! Scanning database schema!")
            
            # Get schema information with progress reporting
            try:
                schema = adapter.get_schema()
                if not schema:
                    self.logger.warning(f"No schema information available for {request.database_name}")
                    return QueryResponse(
                        success=False,
                        sql_query="",
                        result=None,
                        explanation="",
                        error="No schema information available. Database may be empty or inaccessible.",
                        execution_time=time.time() - start_time
                    )
                
                # Report each table found
                for table in schema:
                    report_table(table.name)
                
                report_progress(f"Schema analysis complete! Found {len(schema)} tables")
                
                schema_info = self.prompt_builder.format_schema_info(schema)
                self.logger.info(f"Retrieved schema for {request.database_name}: {schema} tables")
                
            except Exception as schema_error:
                self.logger.error(f"Failed to retrieve schema: {schema_error}")
                return QueryResponse(
                    success=False,
                    sql_query="",
                    result=None,
                    explanation="",
                    error=f"Failed to retrieve database schema: {str(schema_error)}",
                    execution_time=time.time() - start_time
                )
            
            # Generate SQL using LLM with proper prompt and optional provider selection
            try:
                report_progress("AI is analyzing your question!")
                
                # Use specific LLM provider if requested, resolving the provider name
                provider_name = None
                
                if hasattr(request, 'llm_provider') and request.llm_provider:
                    provider_name = self._resolve_llm_provider_name(request.llm_provider)
                    
                    if not provider_name:
                        return QueryResponse(
                            success=False,
                            sql_query="",
                            result=None,
                            explanation="",
                            error=f"LLM connection '{request.llm_provider}' not available. Please check your LLM connections in the Connections tab.",
                            execution_time=time.time() - start_time
                        )
                
                if request.database_type == "mongodb":
                    report_progress("Generating MongoDB aggregation query!")
                    if hasattr(self.llm_client, 'generate_mongodb_query'):
                        # Enhanced client with provider support
                        llm_response = self.llm_client.generate_mongodb_query(schema_info, request.question, provider_name)
                    else:
                        # Legacy client
                        llm_response = self.llm_client.generate_mongodb_query(schema_info, request.question)
                else:
                    report_progress("Crafting SQL query for your request!")
                    if hasattr(self.llm_client, 'generate_sql') and hasattr(self.llm_client, 'providers'):
                        # Enhanced client with provider support
                        llm_response = self.llm_client.generate_sql(schema_info, request.question, provider_name)
                    else:
                        # Legacy client
                        llm_response = self.llm_client.generate_sql(schema_info, request.question)
                
                if not llm_response.success:
                    return QueryResponse(
                        success=False,
                        sql_query="",
                        result=None,
                        explanation="",
                        error=f"LLM generation failed: {llm_response.error}",
                        execution_time=time.time() - start_time
                    )
                
                generated_query = llm_response.content.strip()
                
                # Clean up the generated query
                generated_query = self._clean_generated_query(generated_query)
                
                report_progress(f"Query generated successfully!")
                report_progress(f"Generated Query: {generated_query[:1000]}{'...' if len(generated_query) > 1000 else ''}")
                
                self.logger.info(f"Generated SQL query: {generated_query}")
                
            except Exception as llm_error:
                self.logger.error(f"LLM generation error: {llm_error}")
                return QueryResponse(
                    success=False,
                    sql_query="",
                    result=None,
                    explanation="",
                    error=f"Failed to generate SQL query: {str(llm_error)}",
                    execution_time=time.time() - start_time
                )
            
            # Validate and sanitize the query
            try:
                report_progress("Validating query for security!")
                sanitized_query = adapter.sanitize_query(generated_query)
                report_progress("Query validation passed!")
            except ValueError as validation_error:
                self.logger.error(f"Query validation failed: {validation_error}")
                return QueryResponse(
                    success=False,
                    sql_query=generated_query,
                    result=None,
                    explanation="",
                    error=f"Invalid or potentially dangerous query: {str(validation_error)}",
                    execution_time=time.time() - start_time
                )
            
            # Execute the query with retry logic for MySQL errors
            max_retries = 2
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    report_progress("Executing query against database!")
                    query_result = adapter.execute_query(sanitized_query)
                    
                    if query_result.error:
                        # Check if this is a MySQL error that we can fix with a retry
                        if retry_count < max_retries and self._should_retry_query(query_result.error):
                            report_progress(f"Query issue detected, AI is creating an improved version (attempt {retry_count + 2}/{max_retries + 1})!")
                            
                            # Generate a new query with improved prompt using selected provider
                            retry_prompt = self._create_retry_prompt(schema_info, request.question, query_result.error, generated_query)
                            
                            # Use the same provider for retry as original request
                            if hasattr(self.llm_client, 'generate_sql_custom_prompt') and hasattr(self.llm_client, 'providers'):
                                # Enhanced client with provider support
                                retry_response = self.llm_client.generate_sql_custom_prompt(retry_prompt, provider_name)
                            else:
                                # Legacy client
                                retry_response = self.llm_client.generate_sql_custom_prompt(retry_prompt)
                            
                            if retry_response.success:
                                retry_query = self._clean_generated_query(retry_response.content.strip())
                                try:
                                    sanitized_query = adapter.sanitize_query(retry_query)
                                    generated_query = retry_query  # Update the generated query for final response
                                    report_progress(f"Improved query: {retry_query[:1000]}{'...' if len(retry_query) > 1000 else ''}")
                                    retry_count += 1
                                    continue  # Try again with the new query
                                except ValueError:
                                    pass  # Fall through to original error
                        
                        return QueryResponse(
                            success=False,
                            sql_query=sanitized_query,
                            result=None,
                            explanation="",
                            error=f"Query execution failed: {query_result.error}",
                            execution_time=time.time() - start_time
                        )
                    
                    # Success - break out of retry loop
                    report_progress(f"Query executed successfully! Found {query_result.row_count} rows in {query_result.execution_time:.2f}s")
                    break
                    
                except Exception as exec_error:
                    self.logger.error(f"Query execution error: {exec_error}")
                    return QueryResponse(
                        success=False,
                        sql_query=sanitized_query,
                        result=None,
                        explanation="",
                        error=f"Failed to execute query: {str(exec_error)}",
                        execution_time=time.time() - start_time
                    )
            
            # Generate explanation
            try:
                report_progress("AI is preparing an explanation!")
                explanation_response = self.llm_client.explain_query(sanitized_query)
                explanation = explanation_response.content if explanation_response.success else "Query explanation not available"
                report_progress("Analysis complete!")
            except Exception as explain_error:
                self.logger.warning(f"Failed to generate explanation: {explain_error}")
                explanation = "Query explanation not available"
            
            # Save to history
            try:
                history_entry = QueryHistoryEntry(
                    database_name=request.database_name,
                    question=request.question,
                    generated_query=sanitized_query,
                    execution_time=query_result.execution_time,
                    row_count=query_result.row_count,
                    success=True,
                    error_message=None
                )
                self.history_manager.add_query(history_entry)
            except Exception as history_error:
                self.logger.warning(f"Failed to save to history: {history_error}")
            
            execution_time = time.time() - start_time
            
            return QueryResponse(
                success=True,
                sql_query=sanitized_query,
                result=query_result,
                explanation=explanation,
                error=None,
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error executing natural language query: {e}")
            return QueryResponse(
                success=False,
                sql_query="",
                result=None,
                explanation="",
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def execute_query(self, request: QueryRequest) -> QueryResponse:
        """Execute a query request (alias for execute_natural_language_query)"""
        return self.execute_natural_language_query(request)
    
    def execute_query_with_progress(self, request: QueryRequest, progress_callback=None, table_callback=None) -> QueryResponse:
        """Execute a query request with progress callbacks"""
        return self.execute_natural_language_query_with_progress(request, progress_callback, table_callback)
    
    def get_query_history(self, database_name: Optional[str] = None, limit: int = 50) -> List[QueryHistoryEntry]:
        """Get query history"""
        if database_name:
            return self.history_manager.get_queries_by_database(database_name, limit)
        else:
            return self.history_manager.get_recent_queries(limit)
    
    def get_favorite_queries(self) -> List[QueryHistoryEntry]:
        """Get favorite queries"""
        return self.history_manager.get_favorite_queries()
    
    def toggle_query_favorite(self, query_id: int) -> bool:
        """Toggle favorite status of a query"""
        return self.history_manager.toggle_favorite(query_id)
    
    def search_query_history(self, search_term: str, limit: int = 50) -> List[QueryHistoryEntry]:
        """Search query history"""
        return self.history_manager.search_queries(search_term, limit)
    
    def test_llm_connection(self) -> bool:
        """Test LLM connection"""
        return self.llm_client.health_check()
    
    def get_llm_models(self) -> List[str]:
        """Get available LLM models"""
        models_info = self.llm_client.list_models()
        return [model["name"] for model in models_info.get("models", [])]
    
    def update_llm_model(self, model_name: str) -> bool:
        """Update LLM model"""
        success = self.llm_client.update_model(model_name)
        # Note: In connection-based architecture, model updates should be done 
        # directly on the specific connection configuration
        return success
    
    def _should_retry_query(self, error_message: str) -> bool:
        """Check if we should retry the query based on the error"""
        retry_errors = [
            "1247",  # Reference to group function
            "Reference 'total_salary' not supported",
            "reference to group function",
            "aggregate function",
            "GROUP BY",
        ]
        
        error_lower = error_message.lower()
        return any(retry_error.lower() in error_lower for retry_error in retry_errors)
    
    def _create_retry_prompt(self, schema_info: str, question: str, error_message: str, failed_query: str) -> str:
        """Create an improved prompt for retry based on the error"""
        return f"""You are an expert SQL query generator. The previous query failed with an error. Generate a corrected SQL SELECT query.

### DATABASE SCHEMA ###
{schema_info}

### PREVIOUS FAILED QUERY ###
{failed_query}

### ERROR MESSAGE ###
{error_message}

### SPECIFIC FIXES NEEDED ###
1. If the error mentions "reference to group function", restructure the query to avoid referencing aggregate function results by alias
2. For percentage calculations, use subqueries in the SELECT clause: (SUM(column) / (SELECT SUM(column) FROM table)) * 100
3. Avoid complex nested subqueries that reference group functions from outer queries
4. Use proper GROUP BY clauses for all non-aggregate columns
5. Don't reference aggregate function aliases in the same query level

### RULES ###
1. Only generate SELECT queries
2. Use proper MySQL syntax
3. Include LIMIT clause (max 1000 rows) - MUST be a literal number, not an expression
4. Use table aliases for better readability
5. Ensure all columns in SELECT are either in GROUP BY or are aggregate functions
6. Include only the query result, no additional text or explanations or alternative queries, the query should work as it is with no further modifications
### ORIGINAL QUESTION ###
{question}

### CORRECTED SQL QUERY ###
Generate only the corrected SQL query without any additional text:"""
    
    def _clean_generated_query(self, generated_query: str) -> str:
        """Clean up the generated query by removing markdown and explanatory text"""
        # Clean up the generated query (remove markdown formatting if present)
        if "```javascript" in generated_query or "```mongodb" in generated_query:
            # Extract MongoDB JavaScript from markdown code block
            if "```javascript" in generated_query:
                start_idx = generated_query.find("```javascript") + 13
            else:
                start_idx = generated_query.find("```mongodb") + 10
            end_idx = generated_query.find("```", start_idx)
            if end_idx > start_idx:
                generated_query = generated_query[start_idx:end_idx].strip()
        elif "```sql" in generated_query:
            # Extract SQL from markdown code block
            start_idx = generated_query.find("```sql") + 6
            end_idx = generated_query.find("```", start_idx)
            if end_idx > start_idx:
                generated_query = generated_query[start_idx:end_idx].strip()
        elif "```" in generated_query:
            # Extract from generic code block
            start_idx = generated_query.find("```") + 3
            end_idx = generated_query.find("```", start_idx)
            if end_idx > start_idx:
                generated_query = generated_query[start_idx:end_idx].strip()
        
        # Handle MongoDB queries specifically
        if "db." in generated_query:
            return self._clean_mongodb_query(generated_query)
        
        # Remove any explanatory text before/after the SQL
        lines = generated_query.split('\n')
        sql_lines = []
        in_sql = False
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith(('SELECT', 'WITH', 'SHOW')):
                in_sql = True
            if in_sql and line:
                sql_lines.append(line)
            if in_sql and line.endswith(';'):
                break
        
        if sql_lines:
            generated_query = ' '.join(sql_lines)
            
        return generated_query
    
    def _clean_mongodb_query(self, generated_query: str) -> str:
        """Clean up MongoDB specific queries"""
        import re
        import json
        
        # Remove JavaScript comments
        lines = generated_query.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove inline comments
            if '//' in line:
                line = line[:line.find('//')]
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        query = ' '.join(cleaned_lines)
        
        # Remove semicolon at the end if present
        query = query.rstrip(';')
        
        # Extract collection name and operation
        # Pattern: db.collection.operation(...)
        match = re.match(r'db\.(\w+)\.(\w+)\((.*)\)', query, re.DOTALL)
        if match:
            collection = match.group(1)
            operation = match.group(2)
            params = match.group(3).strip()
            
            if operation == 'aggregate':
                # Extract the aggregation pipeline
                try:
                    # Try to parse the aggregation pipeline as JSON
                    # Remove extra whitespace and format for JSON parsing
                    params = re.sub(r'\s+', ' ', params)
                    
                    # Handle JavaScript object notation vs JSON
                    # Replace unquoted keys with quoted keys for JSON compatibility
                    params = re.sub(r'(\w+):', r'"\1":', params)
                    
                    # Parse as JSON to validate
                    pipeline = json.loads(params)
                    
                    # Return a simplified format for the adapter
                    return f"{collection}.aggregate({json.dumps(pipeline)})"
                    
                except (json.JSONDecodeError, ValueError) as e:
                    self.logger.warning(f"Could not parse MongoDB aggregation pipeline: {e}")
                    # Fall back to simple format
                    return f"{collection}.aggregate"
            
            elif operation in ['find', 'findOne']:
                # Handle find operations
                return f"{collection}.find({params})" if params else f"{collection}.find"
            
            elif operation == 'count':
                return f"{collection}.count"
            
            else:
                return f"{collection}.{operation}"
        
        # If pattern doesn't match, return as is
        return query
    
    def cleanup_old_history(self, days_to_keep: int = 30) -> int:
        """Clean up old query history"""
        return self.history_manager.cleanup_old_queries(days_to_keep)
    
    def export_query_history(self, filepath: str, format: str = "json") -> bool:
        """Export query history"""
        return self.history_manager.export_history(filepath, format)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self.history_manager.get_statistics()
