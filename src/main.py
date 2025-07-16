"""
Main entry point for InsightPilot application
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal

# Add the src directory to Python path to enable absolute imports
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    application_path = sys._MEIPASS
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

from ui.main_window import MainWindow
from api.server_api import run_server
from config.config_manager import ConfigManager


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


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('insightpilot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="InsightPilot - AI-powered data exploration")
    parser.add_argument(
        "--mode",
        choices=["standalone", "client", "server"],
        default="standalone",
        help="Application mode (default: standalone)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host for server mode (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=50051,
        help="Port for server mode (default: 50051)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    return parser.parse_args()


def run_standalone_mode():
    """Run InsightPilot in standalone mode (GUI + local LLM + gRPC server)"""
    app = QApplication(sys.argv)
    app.setApplicationName("InsightPilot")
    app.setApplicationVersion("1.0.0")
    
    # Initialize configuration
    config_manager = ConfigManager()
    
    # Create and show main window
    window = MainWindow(config_manager)
    window.show()
    
    # Start gRPC server in background thread
    server_thread = ServerThread("localhost", 50051, config_manager)
    
    # Connect server signals to handle server events
    def on_server_started(host, port):
        window.status_bar.showMessage(f"Ready - Standalone Mode (Server: {host}:{port})")
        if hasattr(window, 'server_status_label'):
            window.server_status_label.setText(f"Server: Running on {host}:{port}")
            window.server_status_label.setStyleSheet("color: green; font-weight: bold;")
        logging.getLogger(__name__).info(f"gRPC server started on {host}:{port}")
    
    def on_server_error(error):
        window.status_bar.showMessage(f"Server Error: {error}")
        if hasattr(window, 'server_status_label'):
            window.server_status_label.setText(f"Server: Error - {error}")
            window.server_status_label.setStyleSheet("color: red; font-weight: bold;")
        logging.getLogger(__name__).error(f"gRPC server error: {error}")
    
    server_thread.server_started.connect(on_server_started)
    server_thread.server_error.connect(on_server_error)
    
    # Start the server thread
    server_thread.start()
    
    # Store server thread reference to prevent garbage collection
    window.server_thread = server_thread
    
    return app.exec()


def run_client_mode():
    """Run InsightPilot in client mode (GUI only, connects to remote server)"""
    app = QApplication(sys.argv)
    app.setApplicationName("InsightPilot Client")
    app.setApplicationVersion("1.0.0")
    
    # Initialize configuration for client mode
    config_manager = ConfigManager()
    
    # Create and show main window in client mode
    window = MainWindow(config_manager, client_mode=True)
    window.show()
    
    return app.exec()


def run_server_mode(host: str, port: int):
    """Run InsightPilot in server mode (headless, gRPC server)"""
    logging.info(f"Starting InsightPilot server on {host}:{port}")
    
    # Initialize configuration
    config_manager = ConfigManager()
    
    # Start gRPC server
    run_server(host, port, config_manager)


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Setup logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting InsightPilot in {args.mode} mode")
    
    try:
        if args.mode == "standalone":
            return run_standalone_mode()
        elif args.mode == "client":
            return run_client_mode()
        elif args.mode == "server":
            return run_server_mode(args.host, args.port)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
