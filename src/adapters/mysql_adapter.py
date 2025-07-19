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
                'user': self.connection.username,
                'password': self.connection.password,
                'autocommit': True,
                'charset': 'utf8mb4',
                'use_unicode': True,
                'connect_timeout': 30,
                'sql_mode': 'TRADITIONAL',
            }
            
            # Only include database if it's specified and not empty
            if self.connection.database and self.connection.database.strip():
                config['database'] = self.connection.database
            
            # Add custom connection parameters if provided
            if self.connection.connection_params:
                config.update(self.connection.connection_params)
            
            self._conn = mysql.connector.connect(**config)
            
            # If no database was specified, try to select a default one
            if not self.connection.database or not self.connection.database.strip():
                self._select_default_database()
            
            self._connected = True
            db_name = self.connection.database or "No database selected"
            self.logger.info(f"Connected to MySQL server: {db_name}")
            return True
            
        except Error as e:
            self.logger.error(f"MySQL connection error: {e}")
            self._connected = False
            return False
        except Exception as e:
            self.logger.error(f"MySQL connection error: {e}")
            self._connected = False
            return False
    
    def _select_default_database(self):
        """Select a default database if none was specified"""
        try:
            cursor = self._conn.cursor()
            
            # Get list of non-system databases
            cursor.execute("""
                SELECT SCHEMA_NAME 
                FROM information_schema.SCHEMATA 
                WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                ORDER BY SCHEMA_NAME
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                default_db = result[0]
                cursor.execute(f"USE `{default_db}`")
                self.connection.database = default_db
                self.logger.info(f"Selected default database: {default_db}")
            else:
                self.logger.warning("No user databases found, will use information_schema for queries")
                self.connection.database = "information_schema"
                
            cursor.close()
            
        except Error as e:
            self.logger.warning(f"Could not select default database: {e}")
            # Set to empty to handle in schema queries
            self.connection.database = ""
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
            # Determine which databases to scan
            databases_to_scan = []
            
            if self.connection.database and self.connection.database.strip():
                # Use specified database
                databases_to_scan = [self.connection.database]
            else:
                # Get all user databases
                cursor.execute("""
                    SELECT SCHEMA_NAME 
                    FROM information_schema.SCHEMATA 
                    WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                    ORDER BY SCHEMA_NAME
                """)
                databases_to_scan = [row[0] for row in cursor.fetchall()]
                
                if not databases_to_scan:
                    self.logger.warning("No user databases found")
                    return []
            
            # Get tables from each database
            for database_name in databases_to_scan:
                cursor.execute("""
                    SELECT TABLE_NAME 
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """, (database_name,))
                
                tables = cursor.fetchall()
                
                for (table_name,) in tables:
                    # Prefix table name with database if scanning multiple databases
                    display_table_name = table_name
                    if len(databases_to_scan) > 1:
                        display_table_name = f"{database_name}.{table_name}"
                    
                    # Get columns for each table
                    cursor.execute("""
                        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION
                    """, (database_name, table_name))
                    
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
                    """, (database_name, table_name))
                    
                    foreign_keys = []
                    for col_name, ref_table, ref_col in cursor.fetchall():
                        # Include database prefix in reference if scanning multiple databases
                        ref_table_name = ref_table
                        if len(databases_to_scan) > 1:
                            ref_table_name = f"{database_name}.{ref_table}"
                        foreign_keys.append({
                            "column": col_name,
                            "references": f"{ref_table_name}.{ref_col}"
                        })
                    
                    schemas.append(TableSchema(
                        name=display_table_name,
                        columns=columns,
                        primary_keys=primary_keys,
                        foreign_keys=foreign_keys
                    ))
            self.logger.debug(f"the tables found are {(tables)} tables from {len(databases_to_scan)} database(s)")

            self.logger.info(f"Retrieved schema for {len(schemas)} tables from {len(databases_to_scan)} database(s)")
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
            # If no database is currently selected, try to use the connection database
            if self.connection.database and self.connection.database.strip():
                try:
                    cursor.execute(f"USE `{self.connection.database}`")
                except Error as db_error:
                    self.logger.warning(f"Could not use database {self.connection.database}: {db_error}")
            
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
            # Handle specific "No database selected" error
            if e.errno == 1046:  # No database selected
                self.logger.info("No database selected, attempting to use default database")
                try:
                    # Try to select the first available user database
                    cursor.execute("""
                        SELECT SCHEMA_NAME 
                        FROM information_schema.SCHEMATA 
                        WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                        ORDER BY SCHEMA_NAME
                        LIMIT 1
                    """)
                    result = cursor.fetchone()
                    if result:
                        default_db = result[0]
                        cursor.execute(f"USE `{default_db}`")
                        self.connection.database = default_db
                        self.logger.info(f"Switched to default database: {default_db}")
                        
                        # Retry the original query
                        if params:
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)
                        
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []
                        rows = cursor.fetchall()
                        execution_time = time.time() - start_time
                        rows_list = [list(row) for row in rows]
                        
                        return QueryResult(
                            columns=columns,
                            rows=rows_list,
                            row_count=len(rows_list),
                            execution_time=execution_time
                        )
                    else:
                        raise Error("No user databases available", 1046)
                        
                except Error as retry_error:
                    self.logger.error(f"Failed to retry query with default database: {retry_error}")
                    return QueryResult(
                        columns=[],
                        rows=[],
                        row_count=0,
                        execution_time=time.time() - start_time,
                        error=f"No database selected and no default database available: {str(retry_error)}"
                    )
            else:
                self.logger.error(f"MySQL query execution error: {e}")
                
                # Check for common MySQL errors and provide helpful suggestions
                error_suggestion = self._get_error_suggestion(e)
                error_message = f"MySQL Error {e.errno}: {e.msg}"
                if error_suggestion:
                    error_message += f"\n\nSuggestion: {error_suggestion}"
                
                return QueryResult(
                    columns=[],
                    rows=[],
                    row_count=0,
                    execution_time=time.time() - start_time,
                    error=error_message
                )
        finally:
            cursor.close()
    
    def _get_error_suggestion(self, error: Error) -> str:
        """Get suggestion for common MySQL errors"""
        error_suggestions = {
            1247: "This error occurs when referencing a group function result by alias in the same query level. Try using subqueries or restructuring the query to avoid referencing aggregate function aliases.",
            1054: "Column not found. Check column names and table aliases. Make sure all columns exist in the selected tables.",
            1146: "Table doesn't exist. Verify the table name and that you have access to it.",
            1064: "SQL syntax error. Check your SQL syntax, especially around JOINs, WHERE clauses, and function calls.",
            1046: "No database selected. Use 'USE database_name' or specify the database in your connection.",
            1452: "Foreign key constraint fails. Check that referenced values exist in the parent table.",
            1062: "Duplicate entry. The value you're trying to insert already exists for a unique key.",
        }
        
        return error_suggestions.get(error.errno, "Please check your SQL syntax and database schema.")
    
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
        
        # Check for invalid LIMIT clause patterns
        import re
        # Check for LIMIT with expressions (multiplication, subqueries, etc.)
        limit_pattern = r'LIMIT\s+[^0-9\s]|LIMIT\s+\d+\s*[*+\-/]|LIMIT\s+\([^)]*SELECT'
        if re.search(limit_pattern, query_upper, re.IGNORECASE):
            self.logger.warning(f"Invalid LIMIT clause detected in query: {query}")
            return False
        
        return True
    
    def get_table_sample(self, table_name: str, limit: int = 100) -> QueryResult:
        """Get sample data from MySQL table"""
        query = f"SELECT * FROM `{table_name}` LIMIT {limit}"
        return self.execute_query(query)
