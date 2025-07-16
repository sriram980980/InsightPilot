"""
InsightPilot Application Launcher
"""

import sys
import os
import argparse
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal
from config.config_manager import ConfigManager
from ui.main_window import MainWindow
from api.server_api import run_server


class ServerThread(QThread):
    """Thread for running gRPC server in background"""
    server_started = Signal(str, int)
    server_error = Signal(str)
    
    def __init__(self, host: str, port: int, config_manager: ConfigManager):
        super().__init__()
        self.host = host
        self.port = port
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.server_instance = None
        
    def run(self):
        """Run the gRPC server in background thread"""
        try:
            self.logger.info(f"Starting gRPC server thread on {self.host}:{self.port}")
            self.server_started.emit(self.host, self.port)
            
            # Import here to avoid circular imports
            from api.server_api import InsightPilotServer
            
            # Create and start server
            self.server_instance = InsightPilotServer(self.host, self.port, self.config_manager)
            self.server_instance.start()
            
        except Exception as e:
            self.logger.error(f"Server thread error: {e}")
            self.server_error.emit(str(e))
            
    def stop_server(self):
        """Gracefully stop the server"""
        if self.server_instance:
            self.server_instance.stop()


def setup_logging(log_level=logging.INFO):
    """Set up logging configuration"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('insightpilot.log')
        ]
    )


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='InsightPilot - AI-Powered Data Explorer')
    parser.add_argument(
        '--mode',
        choices=['standalone', 'client', 'server'],
        default='standalone',
        help='Launch mode (default: standalone)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--config',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='Host for server mode (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=50051,
        help='Port for server mode (default: 50051)'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting InsightPilot in {args.mode} mode")
    
    if args.mode == 'server':
        # Server mode - headless (no UI)
        logger.info("Starting in headless server mode")
        try:
            config_manager = ConfigManager(args.config)
            run_server(args.host, args.port, config_manager)
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            sys.exit(1)
        return
    
    # Client or standalone mode - start UI
    app = QApplication(sys.argv)
    app.setApplicationName("InsightPilot")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("InsightPilot")
    
    try:
        # Create config manager
        config_manager = ConfigManager(args.config)
        
        # Create main window
        client_mode = (args.mode == 'client')
        window = MainWindow(config_manager, client_mode=client_mode)
        window.show()
        
        # If standalone mode, start gRPC server in background
        if args.mode == 'standalone':
            server_thread = ServerThread(args.host, args.port, config_manager)
            
            # Connect server signals to handle server events
            def on_server_started(host, port):
                window.status_bar.showMessage(f"Ready - Standalone Mode (Server: {host}:{port})")
                if hasattr(window, 'server_status_label'):
                    window.server_status_label.setText(f"Server: Running on {host}:{port}")
                    window.server_status_label.setStyleSheet("color: green; font-weight: bold;")
                logger.info(f"gRPC server started on {host}:{port}")
            
            def on_server_error(error):
                window.status_bar.showMessage(f"Server Error: {error}")
                if hasattr(window, 'server_status_label'):
                    window.server_status_label.setText(f"Server: Error - {error}")
                    window.server_status_label.setStyleSheet("color: red; font-weight: bold;")
                logger.error(f"gRPC server error: {error}")
            
            server_thread.server_started.connect(on_server_started)
            server_thread.server_error.connect(on_server_error)
            
            # Start the server thread
            server_thread.start()
            
            # Store server thread reference to prevent garbage collection
            window.server_thread = server_thread
        
        logger.info("Application started successfully")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
