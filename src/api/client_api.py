"""
Client API for UI-to-LLM/DB communication
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from adapters.base_adapter import BaseDBAdapter, QueryResult, TableSchema
from adapters.mysql_adapter import MySQLAdapter
from adapters.oracle_adapter import OracleAdapter
from adapters.mongo_adapter import MongoAdapter
from llm.llm_client import LLMClient, LLMResponse
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
        
        # Initialize components
        self.llm_client = self._init_llm_client()
        self.prompt_builder = PromptBuilder()
        self.history_manager = HistoryManager()
        
        # Active database adapters
        self.adapters: Dict[str, BaseDBAdapter] = {}
    
    def _init_llm_client(self) -> LLMClient:
        """Initialize LLM client from configuration"""
        llm_settings = self.config_manager.get_llm_settings()
        
        return LLMClient(
            host=llm_settings.get("host", "localhost"),
            port=llm_settings.get("port", 11434),
            model=llm_settings.get("model", "mistral:7b")
        )
    
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
                    col.name: {
                        'type': col.data_type,
                        'nullable': col.nullable
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
                        error=f"Could not connect to database: {request.database_name}",
                        execution_time=time.time() - start_time
                    )
            
            adapter = self.adapters[request.database_name]
            
            # Get schema information
            schema = adapter.get_schema()
            schema_info = self.prompt_builder.format_schema_info(schema)
            
            # Generate SQL using LLM
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
            
            # Execute the query
            query_result = adapter.execute_query(generated_query)
            
            # Generate explanation
            explanation_response = self.llm_client.explain_query(generated_query)
            explanation = explanation_response.content if explanation_response.success else "Query explanation not available"
            
            # Save to history
            history_entry = QueryHistoryEntry(
                database_name=request.database_name,
                question=request.question,
                generated_query=generated_query,
                execution_time=query_result.execution_time,
                row_count=query_result.row_count,
                success=query_result.error is None,
                error_message=query_result.error
            )
            self.history_manager.add_query(history_entry)
            
            execution_time = time.time() - start_time
            
            return QueryResponse(
                success=query_result.error is None,
                sql_query=generated_query,
                result=query_result,
                explanation=explanation,
                error=query_result.error,
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
    
    def cleanup_old_history(self, days_to_keep: int = 30) -> int:
        """Clean up old query history"""
        return self.history_manager.cleanup_old_queries(days_to_keep)
    
    def export_query_history(self, filepath: str, format: str = "json") -> bool:
        """Export query history"""
        return self.history_manager.export_history(filepath, format)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self.history_manager.get_statistics()
