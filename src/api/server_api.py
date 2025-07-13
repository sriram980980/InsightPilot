"""
gRPC server for InsightPilot server mode
"""

import logging
import time
from concurrent import futures
import grpc

from config.config_manager import ConfigManager
from api.client_api import ClientAPI


def run_server(host: str, port: int, config_manager: ConfigManager):
    """Run InsightPilot gRPC server"""
    logger = logging.getLogger(__name__)
    
    # For MVP, we'll implement a basic HTTP server instead of full gRPC
    # This is a placeholder for the actual gRPC implementation
    
    logger.info(f"Starting InsightPilot server on {host}:{port}")
    logger.info("Note: This is a placeholder server implementation")
    logger.info("Full gRPC server will be implemented in production version")
    
    try:
        # Initialize client API for server operations
        client_api = ClientAPI(config_manager)
        
        logger.info("Server components initialized successfully")
        logger.info("Server is ready to accept connections")
        
        # Keep server running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
