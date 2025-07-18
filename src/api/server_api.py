"""
gRPC server for InsightPilot server mode with LLM integration
"""

import logging
import time
import signal
import threading
from concurrent import futures
import grpc

from config.config_manager import ConfigManager
from api.client_api import ClientAPI, QueryRequest as APIQueryRequest
from api import insightpilot_pb2
from api import insightpilot_pb2_grpc


class InsightPilotServiceImpl(insightpilot_pb2_grpc.InsightPilotServiceServicer):
    """gRPC service implementation"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.client_api = ClientAPI(config_manager)
        self.logger = logging.getLogger(__name__)
    
    def GetSchema(self, request, context):
        """Get database schema"""
        try:
            schema = self.client_api.get_schema(
                request.connection_name,
                request.database_type
            )
            
            response = insightpilot_pb2.SchemaResponse()
            response.success = True
            
            # Convert schema to protobuf format
            for table_name, columns in schema.items():
                table_info = response.tables.add()
                table_info.name = table_name
                
                for col_name, col_info in columns.items():
                    column_info = table_info.columns.add()
                    column_info.name = col_name
                    column_info.type = col_info.get('type', 'string')
                    column_info.nullable = col_info.get('nullable', True)
            
            return response
            
        except Exception as e:
            self.logger.error(f"GetSchema error: {e}")
            response = insightpilot_pb2.SchemaResponse()
            response.success = False
            response.error = str(e)
            return response
    
    def ExecuteQuery(self, request, context):
        """Execute natural language query"""
        try:
            # Convert gRPC request to API request
            api_request = APIQueryRequest(
                database_name=request.database_connection,
                question=request.natural_language_query,
                database_type="mysql"  # Will be determined from connection config
            )
            
            # Execute query through client API
            result = self.client_api.execute_query(api_request)
            
            # Convert result to gRPC response
            response = insightpilot_pb2.QueryResponse()
            response.success = result.success
            response.generated_sql = result.sql_query
            response.explanation = result.explanation
            
            if result.error:
                response.error = result.error
            
            if result.result:
                query_result = response.result
                query_result.columns.extend(result.result.columns)
                query_result.total_rows = len(result.result.rows)
                query_result.execution_time = result.execution_time
                
                for row in result.result.rows:
                    query_row = query_result.rows.add()
                    query_row.values.extend([str(v) for v in row])
            
            return response
            
        except Exception as e:
            self.logger.error(f"ExecuteQuery error: {e}")
            response = insightpilot_pb2.QueryResponse()
            response.success = False
            response.error = str(e)
            return response
    
    def ListConnections(self, request, context):
        """List available connections"""
        try:
            connections = self.config_manager.get_connections()
            
            response = insightpilot_pb2.ListConnectionsResponse()
            response.success = True
            
            for conn in connections:
                conn_info = response.connections.add()
                conn_info.name = conn['name']
                conn_info.type = conn.get('type', 'database')
                conn_info.status = "connected"  # TODO: Implement actual status check
            
            return response
            
        except Exception as e:
            self.logger.error(f"ListConnections error: {e}")
            response = insightpilot_pb2.ListConnectionsResponse()
            response.success = False
            response.error = str(e)
            return response
    
    def HealthCheck(self, request, context):
        """Health check endpoint"""
        response = insightpilot_pb2.HealthResponse()
        response.healthy = True
        response.status = "Server is running"
        return response


class InsightPilotServer:
    """InsightPilot gRPC server implementation"""
    
    def __init__(self, host: str, port: int, config_manager: ConfigManager):
        self.host = host
        self.port = port
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.server = None
        self.running = False
        self.service_impl = None
        
    def start(self):
        """Start the gRPC server"""
        try:
            # Initialize service implementation
            self.service_impl = InsightPilotServiceImpl(self.config_manager)
            
            # Create gRPC server
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            
            # Add service to server
            insightpilot_pb2_grpc.add_InsightPilotServiceServicer_to_server(
                self.service_impl, 
                self.server
            )
            
            # Start server
            listen_addr = f'{self.host}:{self.port}'
            self.server.add_insecure_port(listen_addr)
            self.server.start()
            
            self.running = True
            self.logger.info(f"gRPC server started on {listen_addr}")
            self.logger.info("Server is ready to accept connections")
            
            # Keep server running
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Server interrupted by user")
                self.stop()
                
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
            
    def stop(self):
        """Stop the gRPC server"""
        if self.server and self.running:
            self.logger.info("Stopping gRPC server...")
            self.running = False
            self.server.stop(grace=5)
            self.logger.info("gRPC server stopped")


def run_server(host: str, port: int, config_manager: ConfigManager):
    """Run InsightPilot gRPC server"""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting InsightPilot server on {host}:{port}")
    
    # Create and start server
    server = InsightPilotServer(host, port, config_manager)
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        server.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        server.start()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
