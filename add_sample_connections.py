"""
Sample script to add test connections and demonstrate the UI
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.config_manager import ConfigManager


def add_sample_connections():
    """Add sample connections for testing"""
    config_manager = ConfigManager()
    
    # Sample MySQL connection
    mysql_config = {
        'type': 'MySQL',
        'host': '127.0.0.1',
        'port': 3306,
        'username': 'root',
        'password': '',
        'database': 'sakila',
        'timeout': 30,
        'autocommit': True
    }
    
    # Sample Oracle connection
    oracle_config = {
        'type': 'Oracle',
        'host': 'localhost',
        'port': 1521,
        'username': 'hr',
        'password': '',
        'service_name': 'XE',
        'timeout': 30,
        'autocommit': True
    }
    
    try:
        config_manager.save_connection("Local MySQL", mysql_config)
        config_manager.save_connection("Local Oracle", oracle_config)
        print("Sample connections added successfully!")
        print("- Local MySQL (127.0.0.1:3306)")
        print("- Local Oracle (localhost:1521)")
        print("\nYou can now run the application and see these connections in the Connections tab.")
        
    except Exception as e:
        print(f"Error adding sample connections: {e}")


if __name__ == "__main__":
    add_sample_connections()
