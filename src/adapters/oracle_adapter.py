"""
Oracle database adapter
"""

import logging
import time
from typing import Dict, List, Any, Optional
import oracledb

from .base_adapter import BaseDBAdapter, DBConnection, TableSchema, QueryResult


class OracleAdapter(BaseDBAdapter):
    """Oracle database adapter implementation"""
    
    def __init__(self, connection: DBConnection):
        super().__init__(connection)
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Establish Oracle connection"""
        try:
            # Configure Oracle connection
            dsn = f"{self.connection.host}:{self.connection.port}/{self.connection.database}"
            
            self._conn = oracledb.connect(
                user=self.connection.username,
                password=self.connection.password,
                dsn=dsn,
                **(self.connection.connection_params or {})
            )
            
            self._connected = True
            self.logger.info(f"Connected to Oracle database: {self.connection.database}")
            return True
            
        except oracledb.Error as e:
            self.logger.error(f"Oracle connection error: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Close Oracle connection"""
        if self._conn:
            self._conn.close()
            self._connected = False
            self.logger.info("Oracle connection closed")
    
    def test_connection(self) -> bool:
        """Test Oracle connection"""
        try:
            if not self._connected:
                return self.connect()
            
            cursor = self._conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
            cursor.close()
            return True
            
        except oracledb.Error as e:
            self.logger.error(f"Oracle connection test failed: {e}")
            return False
    
    def get_schema(self) -> List[TableSchema]:
        """Retrieve Oracle schema information"""
        if not self._connected:
            raise ConnectionError("Not connected to Oracle database")
        
        schemas = []
        cursor = self._conn.cursor()
        
        try:
            # Get all tables for current user
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM USER_TABLES 
                ORDER BY TABLE_NAME
            """)
            
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                # Get columns for each table
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, NULLABLE, DATA_DEFAULT
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = :table_name
                    ORDER BY COLUMN_ID
                """, {"table_name": table_name})
                
                columns = []
                for col_name, data_type, nullable, default in cursor.fetchall():
                    columns.append({
                        "name": col_name,
                        "type": data_type,
                        "nullable": nullable == "Y",
                        "default": default
                    })
                
                # Get primary keys
                cursor.execute("""
                    SELECT COLUMN_NAME
                    FROM USER_CONS_COLUMNS
                    WHERE TABLE_NAME = :table_name
                    AND CONSTRAINT_NAME IN (
                        SELECT CONSTRAINT_NAME
                        FROM USER_CONSTRAINTS
                        WHERE TABLE_NAME = :table_name
                        AND CONSTRAINT_TYPE = 'P'
                    )
                """, {"table_name": table_name})
                
                primary_keys = [row[0] for row in cursor.fetchall()]
                
                # Get foreign keys
                cursor.execute("""
                    SELECT a.COLUMN_NAME, b.TABLE_NAME, b.COLUMN_NAME
                    FROM USER_CONS_COLUMNS a
                    JOIN USER_CONSTRAINTS c ON a.CONSTRAINT_NAME = c.CONSTRAINT_NAME
                    JOIN USER_CONS_COLUMNS b ON c.R_CONSTRAINT_NAME = b.CONSTRAINT_NAME
                    WHERE a.TABLE_NAME = :table_name
                    AND c.CONSTRAINT_TYPE = 'R'
                """, {"table_name": table_name})
                
                foreign_keys = []
                for col_name, ref_table, ref_col in cursor.fetchall():
                    foreign_keys.append({
                        "column": col_name,
                        "references": f"{ref_table}.{ref_col}"
                    })
                
                schemas.append(TableSchema(
                    name=table_name,
                    columns=columns,
                    primary_keys=primary_keys,
                    foreign_keys=foreign_keys
                ))
            
            return schemas
            
        except oracledb.Error as e:
            self.logger.error(f"Error retrieving Oracle schema: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute Oracle query and return results"""
        if not self._connected:
            raise ConnectionError("Not connected to Oracle database")
        
        # Sanitize and validate query
        query = self.sanitize_query(query)
        if not self.validate_query(query):
            raise ValueError(f"Invalid or potentially dangerous query '{query}'")
        
        cursor = self._conn.cursor()
        start_time = time.time()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            execution_time = time.time() - start_time
            
            # Convert rows to list of lists for consistency
            rows_list = [list(row) for row in rows]
            
            return QueryResult(
                columns=columns,
                rows=rows_list,
                row_count=len(rows_list),
                execution_time=execution_time
            )
            
        except oracledb.Error as e:
            self.logger.error(f"Oracle query execution error: {e}")
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                execution_time=time.time() - start_time,
                error=str(e)
            )
        finally:
            cursor.close()
    
    def validate_query(self, query: str) -> bool:
        """Validate Oracle query for safety"""
        query_upper = query.upper().strip()
        
        # Only allow SELECT statements
        if not query_upper.startswith('SELECT'):
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = [
            'UTL_FILE', 'UTL_HTTP', 'DBMS_', 'UTL_TCP', 'UTL_SMTP',
            'SYSTEM', 'EXEC', 'EXECUTE', 'BEGIN', 'DECLARE'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in query_upper:
                return False
        
        return True
    
    def get_table_sample(self, table_name: str, limit: int = 100) -> QueryResult:
        """Get sample data from Oracle table"""
        query = f"SELECT * FROM {table_name} WHERE ROWNUM <= {limit}"
        return self.execute_query(query)
