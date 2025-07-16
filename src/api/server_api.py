"""
gRPC server for InsightPilot server mode
"""

import logging
import time
import signal
import threading
from concurrent import futures
import grpc

from config.config_manager import ConfigManager
from api.client_api import ClientAPI


class InsightPilotServer:
    """InsightPilot gRPC server implementation"""
    
    def __init__(self, host: str, port: int, config_manager: ConfigManager):
        self.host = host
        self.port = port
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.server = None
        self.running = False
        self.client_api = None
        
    def start(self):
        """Start the gRPC server"""
        try:
            # Initialize client API for server operations
            self.client_api = ClientAPI(self.config_manager)
            
            # Create gRPC server
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            
            # Add service implementations here (placeholder for now)
            # TODO: Add actual gRPC service definitions and implementations
            
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
