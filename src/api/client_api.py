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
        return {
            name: {
                "host": conn.host,
                "port": conn.port,
                "database": conn.database,
                "type": self._detect_db_type(conn.port)
            }
            for name, conn in self.config_manager.get_database_connections().items()
        }
    
    def _detect_db_type(self, port: int) -> str:
        """Detect database type from port"""
        if port == 3306:
            return "mysql"
        elif port == 1521:
            return "oracle"
        elif port == 27017:
            return "mongodb"
        else:
            return "unknown"
    
    def connect_to_database(self, database_name: str) -> bool:
        """Connect to a specific database"""
        try:
            connections = self.config_manager.get_database_connections()
            
            if database_name not in connections:
                self.logger.error(f"Database connection not found: {database_name}")
                return False
            
            connection = connections[database_name]
            db_type = self._detect_db_type(connection.port)
            
            # Create appropriate adapter
            if db_type == "mysql":
                adapter = MySQLAdapter(connection)
            elif db_type == "oracle":
                adapter = OracleAdapter(connection)
            elif db_type == "mongodb":
                adapter = MongoAdapter(connection)
            else:
                self.logger.error(f"Unsupported database type for {database_name}")
                return False
            
            # Test connection
            if adapter.connect():
                self.adapters[database_name] = adapter
                self.logger.info(f"Connected to database: {database_name}")
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
    
    def execute_natural_language_query(self, request: QueryRequest) -> QueryResponse:
        """Execute a natural language query"""
        import time
        start_time = time.time()
        
        try:
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
            
            # Get schema information
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
                
                schema_info = self.prompt_builder.format_schema_info(schema)
                self.logger.info(f"Retrieved schema for {request.database_name}: {len(schema)} tables")
                
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
            
            # Generate SQL using LLM with proper prompt
            try:
                if request.database_type == "mongodb":
                    llm_response = self.llm_client.generate_mongodb_query(schema_info, request.question)
                else:
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
                sanitized_query = adapter.sanitize_query(generated_query)
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
                    query_result = adapter.execute_query(sanitized_query)
                    
                    if query_result.error:
                        # Check if this is a MySQL error that we can fix with a retry
                        if retry_count < max_retries and self._should_retry_query(query_result.error):
                            self.logger.info(f"Retrying query due to MySQL error: {query_result.error}")
                            
                            # Generate a new query with improved prompt
                            retry_prompt = self._create_retry_prompt(schema_info, request.question, query_result.error, generated_query)
                            retry_response = self.llm_client.generate_sql_custom_prompt(retry_prompt)
                            
                            if retry_response.success:
                                retry_query = self._clean_generated_query(retry_response.content.strip())
                                try:
                                    sanitized_query = adapter.sanitize_query(retry_query)
                                    generated_query = retry_query  # Update the generated query for final response
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
                explanation_response = self.llm_client.explain_query(sanitized_query)
                explanation = explanation_response.content if explanation_response.success else "Query explanation not available"
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
        if success:
            # Update configuration
            self.config_manager.update_llm_settings({"model": model_name})
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
3. Include LIMIT clause (max 1000 rows)
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
        if "```sql" in generated_query:
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
    
    def cleanup_old_history(self, days_to_keep: int = 30) -> int:
        """Clean up old query history"""
        return self.history_manager.cleanup_old_queries(days_to_keep)
    
    def export_query_history(self, filepath: str, format: str = "json") -> bool:
        """Export query history"""
        return self.history_manager.export_history(filepath, format)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self.history_manager.get_statistics()
