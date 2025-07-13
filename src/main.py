"""
Main entry point for InsightPilot application
"""

import sys
import argparse
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from api.server_api import run_server
from config.config_manager import ConfigManager


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
    """Run InsightPilot in standalone mode (GUI + local LLM)"""
    app = QApplication(sys.argv)
    app.setApplicationName("InsightPilot")
    app.setApplicationVersion("1.0.0")
    
    # Initialize configuration
    config_manager = ConfigManager()
    
    # Create and show main window
    window = MainWindow(config_manager)
    window.show()
    
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
