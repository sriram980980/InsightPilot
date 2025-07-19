"""
MongoDB database adapter
"""

import logging
import time
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

from .base_adapter import BaseDBAdapter, DBConnection, TableSchema, QueryResult


class MongoAdapter(BaseDBAdapter):
    """MongoDB database adapter implementation"""
    
    def __init__(self, connection: DBConnection):
        super().__init__(connection)
        self.logger = logging.getLogger(__name__)
        self.db = None
    
    def connect(self) -> bool:
        """Establish MongoDB connection"""
        try:
            # Build MongoDB connection string
            if self.connection.username and self.connection.password:
                conn_str = f"mongodb://{self.connection.username}:{self.connection.password}@{self.connection.host}:{self.connection.port}/{self.connection.database}"
            else:
                conn_str = f"mongodb://{self.connection.host}:{self.connection.port}/{self.connection.database}"
            
            # Add connection parameters
            conn_params = self.connection.connection_params or {}
            self._conn = MongoClient(conn_str, **conn_params)
            
            # Select database
            self.db = self._conn[self.connection.database]
            
            # Test connection
            self._conn.admin.command('ping')
            self._connected = True
            self.logger.info(f"Connected to MongoDB database: {self.connection.database}")
            return True
            
        except ConnectionFailure as e:
            self.logger.error(f"MongoDB connection error: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self._conn:
            self._conn.close()
            self._connected = False
            self.logger.info("MongoDB connection closed")
    
    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            if not self._connected:
                return self.connect()
            
            self._conn.admin.command('ping')
            return True
            
        except ConnectionFailure as e:
            self.logger.error(f"MongoDB connection test failed: {e}")
            return False
    
    def get_schema(self) -> List[TableSchema]:
        """Retrieve MongoDB schema information (collections and sample documents)"""
        if not self._connected:
            raise ConnectionError("Not connected to MongoDB database")
        
        schemas = []
        
        try:
            # Get all collections
            collections = self.db.list_collection_names()
            
            for collection_name in collections:
                collection = self.db[collection_name]
                
                # Sample documents to infer schema
                sample_docs = list(collection.find().limit(10))
                
                if not sample_docs:
                    continue
                
                # Infer schema from sample documents
                columns = []
                all_fields = set()
                
                for doc in sample_docs:
                    all_fields.update(doc.keys())
                
                for field in sorted(all_fields):
                    # Determine field type from samples
                    field_types = set()
                    for doc in sample_docs:
                        if field in doc:
                            field_types.add(type(doc[field]).__name__)
                    
                    columns.append({
                        "name": field,
                        "type": ", ".join(field_types),
                        "nullable": not all(field in doc for doc in sample_docs),
                        "default": None
                    })
                
                # MongoDB always has _id as primary key
                primary_keys = ["_id"] if "_id" in all_fields else []
                
                schemas.append(TableSchema(
                    name=collection_name,
                    columns=columns,
                    primary_keys=primary_keys,
                    foreign_keys=[]  # MongoDB doesn't have explicit foreign keys
                ))
            
            return schemas
            
        except PyMongoError as e:
            self.logger.error(f"Error retrieving MongoDB schema: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute MongoDB aggregation query and return results"""
        if not self._connected:
            raise ConnectionError("Not connected to MongoDB database")
        
        start_time = time.time()
        
        try:
            # Parse query to extract collection and operation
            results = self._parse_and_execute_query(query)
            
            execution_time = time.time() - start_time
            
            # Convert results to tabular format
            if results:
                # Get all unique fields from results
                all_fields = set()
                for doc in results:
                    if isinstance(doc, dict):
                        all_fields.update(doc.keys())
                
                columns = sorted(all_fields) if all_fields else ["result"]
                rows = []
                
                if all_fields:
                    # Normal document results
                    for doc in results:
                        row = []
                        for field in columns:
                            value = doc.get(field, None)
                            # Convert complex types to strings
                            if isinstance(value, (dict, list)):
                                value = str(value)
                            elif value is None:
                                value = ""
                            row.append(value)
                        rows.append(row)
                else:
                    # Simple value results (e.g., count)
                    for result in results:
                        rows.append([str(result)])
                
                return QueryResult(
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    execution_time=execution_time
                )
            else:
                return QueryResult(
                    columns=["result"],
                    rows=[["No results found"]],
                    row_count=0,
                    execution_time=execution_time
                )
            
        except Exception as e:
            self.logger.error(f"MongoDB query execution error: {e}")
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _parse_and_execute_query(self, query: str) -> List[Any]:
        """Parse and execute MongoDB query"""
        import json
        import re
        
        # Handle different query formats
        if query.startswith('{') or query.startswith('['):
            # Direct aggregation pipeline or find query
            try:
                pipeline = json.loads(query)
                # Assume it's for the first collection found in schema
                collections = self.db.list_collection_names()
                if collections:
                    collection = self.db[collections[0]]
                    if isinstance(pipeline, list):
                        return list(collection.aggregate(pipeline))
                    else:
                        return list(collection.find(pipeline).limit(1000))
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON query: {query}")
        
        # Parse collection.operation format
        parts = query.split('.')
        if len(parts) < 2:
            raise ValueError(f"Invalid MongoDB query format: {query}")
        
        collection_name = parts[0]
        operation_with_params = '.'.join(parts[1:])
        
        # Extract operation and parameters
        operation_match = re.match(r'(\w+)(?:\((.*)\))?', operation_with_params, re.DOTALL)
        if not operation_match:
            raise ValueError(f"Could not parse operation: {operation_with_params}")
        
        operation = operation_match.group(1)
        params_str = operation_match.group(2) if operation_match.group(2) else ""
        
        collection = self.db[collection_name]
        
        if operation == 'find':
            if params_str:
                try:
                    params = json.loads(params_str)
                    return list(collection.find(params).limit(1000))
                except json.JSONDecodeError:
                    return list(collection.find().limit(1000))
            else:
                return list(collection.find().limit(1000))
        
        elif operation == 'aggregate':
            if params_str:
                try:
                    pipeline = json.loads(params_str)
                    if not isinstance(pipeline, list):
                        pipeline = [pipeline]
                    return list(collection.aggregate(pipeline))
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse aggregation pipeline: {e}")
                    # Fall back to simple aggregation
                    return list(collection.aggregate([{"$limit": 1000}]))
            else:
                # Simple aggregation to get all documents
                return list(collection.aggregate([{"$limit": 1000}]))
        
        elif operation == 'count':
            count_result = collection.count_documents({})
            return [{"count": count_result}]
        
        elif operation == 'findOne':
            result = collection.find_one()
            return [result] if result else []
        
        else:
            raise ValueError(f"Unsupported MongoDB operation: {operation}")
    
    def validate_query(self, query: str) -> bool:
        """Validate MongoDB query for safety"""
        # Basic validation for MongoDB queries
        dangerous_patterns = [
            'eval', 'mapreduce', 'group', '$where'
        ]
        
        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                return False
        
        return True
    
    def get_table_sample(self, table_name: str, limit: int = 100) -> QueryResult:
        """Get sample data from MongoDB collection"""
        if not self._connected:
            raise ConnectionError("Not connected to MongoDB database")
        
        try:
            collection = self.db[table_name]
            documents = list(collection.find().limit(limit))
            
            if not documents:
                return QueryResult(
                    columns=[],
                    rows=[],
                    row_count=0,
                    execution_time=0.0
                )
            
            # Convert to tabular format
            all_fields = set()
            for doc in documents:
                all_fields.update(doc.keys())
            
            columns = sorted(all_fields)
            rows = []
            
            for doc in documents:
                row = []
                for field in columns:
                    value = doc.get(field, None)
                    # Convert complex types to strings
                    if isinstance(value, (dict, list)):
                        value = str(value)
                    row.append(value)
                rows.append(row)
            
            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time=0.0
            )
            
        except PyMongoError as e:
            self.logger.error(f"Error getting MongoDB sample: {e}")
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                execution_time=0.0,
                error=str(e)
            )
