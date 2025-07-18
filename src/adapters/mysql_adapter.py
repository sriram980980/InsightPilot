"""
MySQL database adapter
"""

import logging
import time
from typing import Dict, List, Any, Optional
import mysql.connector
from mysql.connector import Error

from .base_adapter import BaseDBAdapter, DBConnection, TableSchema, QueryResult


class MySQLAdapter(BaseDBAdapter):
    """MySQL database adapter implementation"""
    
    def __init__(self, connection: DBConnection):
        super().__init__(connection)
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Establish MySQL connection"""
        try:
            config = {
                'host': self.connection.host,
                'port': self.connection.port,
                'database': self.connection.database,
                'user': self.connection.username,
                'password': self.connection.password,
                'autocommit': True,
                'charset': 'utf8mb4',
                'use_unicode': True,
                'connect_timeout': 30,
                'sql_mode': 'TRADITIONAL',
            }
            
            # Add custom connection parameters if provided
            if self.connection.connection_params:
                config.update(self.connection.connection_params)
            
            self._conn = mysql.connector.connect(**config)
            self._connected = True
            self.logger.info(f"Connected to MySQL database: {self.connection.database}")
            return True
            
        except Error as e:
            self.logger.error(f"MySQL connection error: {e}")
            self._connected = False
            return False
        except Exception as e:
            self.logger.error(f"MySQL connection error: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Close MySQL connection"""
        if self._conn and self._conn.is_connected():
            self._conn.close()
            self._connected = False
            self.logger.info("MySQL connection closed")
    
    def test_connection(self) -> bool:
        """Test MySQL connection"""
        try:
            if not self._connected:
                return self.connect()
            
            cursor = self._conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
            
        except Error as e:
            self.logger.error(f"MySQL connection test failed: {e}")
            return False
    
    def get_schema(self) -> List[TableSchema]:
        """Retrieve MySQL schema information"""
        if not self._connected:
            raise ConnectionError("Not connected to MySQL database")
        
        schemas = []
        cursor = self._conn.cursor()
        
        try:
            # Get all tables
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            """, (self.connection.database,))
            
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                # Get columns for each table
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (self.connection.database, table_name))
                
                columns = []
                primary_keys = []
                
                for col_name, data_type, is_nullable, default, key in cursor.fetchall():
                    columns.append({
                        "name": col_name,
                        "type": data_type,
                        "nullable": is_nullable == "YES",
                        "default": default
                    })
                    
                    if key == "PRI":
                        primary_keys.append(col_name)
                
                # Get foreign keys
                cursor.execute("""
                    SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s 
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """, (self.connection.database, table_name))
                
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
            
        except Error as e:
            self.logger.error(f"Error retrieving MySQL schema: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute MySQL query and return results"""
        if not self._connected:
            raise ConnectionError("Not connected to MySQL database")
        
        # Sanitize and validate query
        query = self.sanitize_query(query)
        if not self.validate_query(query):
            raise ValueError(f"Invalid or potentially dangerous query, query: {query}")
        
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
            
        except Error as e:
            self.logger.error(f"MySQL query execution error: {e}")
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
        """Validate MySQL query for safety"""
        query_upper = query.upper().strip()
        
        # Only allow SELECT statements
        if not query_upper.startswith('SELECT'):
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = [
            'INTO OUTFILE', 'INTO DUMPFILE', 'LOAD_FILE', 'SYSTEM',
            'EXEC', 'EXECUTE', 'sp_', 'xp_', 'cmdshell'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in query_upper:
                return False
        
        return True
    
    def get_table_sample(self, table_name: str, limit: int = 100) -> QueryResult:
        """Get sample data from MySQL table"""
        query = f"SELECT * FROM `{table_name}` LIMIT {limit}"
        return self.execute_query(query)
