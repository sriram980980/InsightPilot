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
from config.config_manager import ConfigManager
from ui.main_window import MainWindow


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
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting InsightPilot in {args.mode} mode")
    
    if args.mode == 'server':
        # Server mode - headless (no UI)
        logger.info("Starting in headless server mode")
        print("Server mode is not yet implemented.")
        print("This would start a headless gRPC server with LLM + DB adapters.")
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
        
        logger.info("Application started successfully")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
