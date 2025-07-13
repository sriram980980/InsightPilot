"""
Abstract base class for database adapters
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class DBConnection:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    connection_params: Optional[Dict[str, Any]] = None


@dataclass
class TableSchema:
    """Database table schema information"""
    name: str
    columns: List[Dict[str, str]]  # [{"name": "id", "type": "int"}, ...]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, str]]  # [{"column": "user_id", "references": "users.id"}]


@dataclass
class QueryResult:
    """Query execution result"""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time: float
    error: Optional[str] = None


class BaseDBAdapter(ABC):
    """Abstract base class for database adapters"""
    
    def __init__(self, connection: DBConnection):
        self.connection = connection
        self._conn = None
        self._connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test database connection"""
        pass
    
    @abstractmethod
    def get_schema(self) -> List[TableSchema]:
        """Retrieve database schema information"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute SQL query and return results"""
        pass
    
    @abstractmethod
    def validate_query(self, query: str) -> bool:
        """Validate SQL query for safety (deny DDL/DML operations)"""
        pass
    
    @abstractmethod
    def get_table_sample(self, table_name: str, limit: int = 100) -> QueryResult:
        """Get sample data from a table"""
        pass
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._connected
    
    def sanitize_query(self, query: str) -> str:
        """Sanitize SQL query to prevent injection"""
        # Remove dangerous SQL keywords
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
            'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE', 'SET', 'SHOW'
        ]
        
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(f"Dangerous SQL keyword '{keyword}' detected in query")
        
        return query.strip()
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
