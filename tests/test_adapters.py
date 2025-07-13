"""
Tests for database adapters
"""

import pytest
import unittest.mock as mock
from adapters.base_adapter import BaseDBAdapter, DBConnection, QueryResult
from adapters.mysql_adapter import MySQLAdapter
from adapters.oracle_adapter import OracleAdapter
from adapters.mongo_adapter import MongoAdapter


class TestBaseDBAdapter:
    """Test base database adapter functionality"""
    
    def test_db_connection_creation(self):
        """Test DBConnection creation"""
        conn = DBConnection(
            host="localhost",
            port=3306,
            database="testdb",
            username="user",
            password="pass"
        )
        
        assert conn.host == "localhost"
        assert conn.port == 3306
        assert conn.database == "testdb"
        assert conn.username == "user"
        assert conn.password == "pass"
    
    def test_query_result_creation(self):
        """Test QueryResult creation"""
        result = QueryResult(
            columns=["id", "name"],
            rows=[[1, "John"], [2, "Jane"]],
            row_count=2,
            execution_time=0.5
        )
        
        assert result.columns == ["id", "name"]
        assert result.rows == [[1, "John"], [2, "Jane"]]
        assert result.row_count == 2
        assert result.execution_time == 0.5
        assert result.error is None
    
    def test_sanitize_query(self):
        """Test query sanitization"""
        # Create a mock concrete implementation
        class MockAdapter(BaseDBAdapter):
            def connect(self): pass
            def disconnect(self): pass
            def test_connection(self): pass
            def get_schema(self): pass
            def execute_query(self, query, params=None): pass
            def validate_query(self, query): pass
            def get_table_sample(self, table_name, limit=100): pass
        
        conn = DBConnection("localhost", 3306, "test", "user", "pass")
        adapter = MockAdapter(conn)
        
        # Test safe query
        safe_query = "SELECT * FROM users WHERE id = 1"
        assert adapter.sanitize_query(safe_query) == safe_query
        
        # Test dangerous queries
        dangerous_queries = [
            "DROP TABLE users",
            "DELETE FROM users",
            "UPDATE users SET name = 'test'",
            "INSERT INTO users VALUES (1, 'test')"
        ]
        
        for query in dangerous_queries:
            with pytest.raises(ValueError):
                adapter.sanitize_query(query)


class TestMySQLAdapter:
    """Test MySQL adapter functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.connection = DBConnection(
            host="localhost",
            port=3306,
            database="testdb",
            username="user",
            password="pass"
        )
        self.adapter = MySQLAdapter(self.connection)
    
    @mock.patch('adapters.mysql_adapter.mysql.connector.connect')
    def test_connect_success(self, mock_connect):
        """Test successful MySQL connection"""
        mock_conn = mock.Mock()
        mock_connect.return_value = mock_conn
        
        result = self.adapter.connect()
        
        assert result is True
        assert self.adapter._connected is True
        mock_connect.assert_called_once()
    
    @mock.patch('adapters.mysql_adapter.mysql.connector.connect')
    def test_connect_failure(self, mock_connect):
        """Test MySQL connection failure"""
        mock_connect.side_effect = Exception("Connection failed")
        
        result = self.adapter.connect()
        
        assert result is False
        assert self.adapter._connected is False
    
    def test_validate_query_safe(self):
        """Test query validation for safe queries"""
        safe_queries = [
            "SELECT * FROM users",
            "SELECT id, name FROM users WHERE status = 'active'",
            "SELECT COUNT(*) FROM orders"
        ]
        
        for query in safe_queries:
            assert self.adapter.validate_query(query) is True
    
    def test_validate_query_unsafe(self):
        """Test query validation for unsafe queries"""
        unsafe_queries = [
            "UPDATE users SET name = 'test'",
            "DELETE FROM users",
            "INSERT INTO users VALUES (1, 'test')",
            "DROP TABLE users"
        ]
        
        for query in unsafe_queries:
            assert self.adapter.validate_query(query) is False


class TestOracleAdapter:
    """Test Oracle adapter functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.connection = DBConnection(
            host="localhost",
            port=1521,
            database="ORCL",
            username="user",
            password="pass"
        )
        self.adapter = OracleAdapter(self.connection)
    
    @mock.patch('adapters.oracle_adapter.oracledb.connect')
    def test_connect_success(self, mock_connect):
        """Test successful Oracle connection"""
        mock_conn = mock.Mock()
        mock_connect.return_value = mock_conn
        
        result = self.adapter.connect()
        
        assert result is True
        assert self.adapter._connected is True
        mock_connect.assert_called_once()
    
    def test_validate_query_safe(self):
        """Test query validation for safe queries"""
        safe_queries = [
            "SELECT * FROM users",
            "SELECT id, name FROM users WHERE status = 'active'",
            "SELECT COUNT(*) FROM orders"
        ]
        
        for query in safe_queries:
            assert self.adapter.validate_query(query) is True
    
    def test_validate_query_unsafe(self):
        """Test query validation for unsafe queries"""
        unsafe_queries = [
            "UPDATE users SET name = 'test'",
            "DELETE FROM users",
            "INSERT INTO users VALUES (1, 'test')",
            "DROP TABLE users",
            "BEGIN DBMS_OUTPUT.PUT_LINE('test'); END;"
        ]
        
        for query in unsafe_queries:
            assert self.adapter.validate_query(query) is False


class TestMongoAdapter:
    """Test MongoDB adapter functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.connection = DBConnection(
            host="localhost",
            port=27017,
            database="testdb",
            username="user",
            password="pass"
        )
        self.adapter = MongoAdapter(self.connection)
    
    @mock.patch('adapters.mongo_adapter.MongoClient')
    def test_connect_success(self, mock_client):
        """Test successful MongoDB connection"""
        mock_conn = mock.MagicMock()
        mock_client.return_value = mock_conn
        mock_conn.admin.command.return_value = True
        
        # Mock the database access
        mock_db = mock.Mock()
        mock_conn.__getitem__.return_value = mock_db
        
        result = self.adapter.connect()
        
        assert result is True
        assert self.adapter._connected is True
        mock_client.assert_called_once()
    
    def test_validate_query_safe(self):
        """Test query validation for safe queries"""
        safe_queries = [
            "users.find()",
            "orders.aggregate([{'$match': {'status': 'active'}}])",
            "products.find({'price': {'$gt': 100}})"
        ]
        
        for query in safe_queries:
            assert self.adapter.validate_query(query) is True
    
    def test_validate_query_unsafe(self):
        """Test query validation for unsafe queries"""
        unsafe_queries = [
            "users.eval('function() { return 1; }')",
            "orders.mapReduce(function() {}, function() {})",
            "products.group({key: {}, reduce: function() {}})"
        ]
        
        for query in unsafe_queries:
            assert self.adapter.validate_query(query) is False


if __name__ == "__main__":
    pytest.main([__file__])
