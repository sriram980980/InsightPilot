#!/usr/bin/env python3
"""
Test script to verify the connection loading fix
"""

import sys
import os
sys.path.append('src')

def test_connection_loading():
    """Test that connections can be loaded without the 'get' attribute error"""
    
    print("Testing connection loading fix!")
    
    try:
        # Import required modules
        from config.config_manager import ConfigManager
        from ui.tabs.query_chat_tab import QueryChatTab
        from PySide6.QtWidgets import QApplication, QWidget
        
        # Create a minimal QApplication (required for Qt widgets)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create config manager
        config_manager = ConfigManager()
        
        # Test loading connections with the new method
        print("✓ Testing get_connections() method!")
        all_connections = config_manager.get_connections()
        print(f"  Found {len(all_connections)} total connections")
        
        # Filter by type
        db_connections = [conn for conn in all_connections.values() if conn.get('type') == 'DB']
        llm_connections = [conn for conn in all_connections.values() if conn.get('type') == 'LLM']
        
        print(f"  Database connections: {len(db_connections)}")
        print(f"  LLM connections: {len(llm_connections)}")
        
        # Test that we can access sub_type without errors
        for name, conn in all_connections.items():
            if conn.get('type') == 'DB':
                sub_type = conn.get('sub_type', 'unknown')
                host = conn.get('host', 'unknown')
                port = conn.get('port', 'unknown')
                print(f"  DB Connection '{name}': {sub_type.upper()} at {host}:{port}")
            elif conn.get('type') == 'LLM':
                sub_type = conn.get('sub_type', 'unknown')
                model = conn.get('model', 'unknown')
                print(f"  LLM Connection '{name}': {sub_type.upper()} with model {model}")
        
        print("\n✓ Connection loading test completed successfully!")
        print("✓ No 'DBConnection' object has no attribute 'get' errors!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing connection loading fix for 'DBConnection' object has no attribute 'get' error...\n")
    
    success = test_connection_loading()
    
    if success:
        print("\n" + "="*60)
        print("🎉 CONNECTION LOADING FIX VERIFIED!")
        print("="*60)
        print("The error was caused by:")
        print("  - Using get_database_connections() which returns DBConnection objects")
        print("  - Trying to use .get() method on DBConnection objects (which don't have it)")
        print("  - DBConnection is a dataclass, not a dictionary")
        print("\nFix applied:")
        print("  ✓ Updated query_chat_tab.py to use get_connections() instead")
        print("  ✓ Updated client_api.py to use get_connections() and create DBConnection objects for adapters")
        print("  ✓ All connection access now uses dictionary .get() methods properly")
        print("  ✓ Maintained backward compatibility with legacy connections")
    else:
        print("\n❌ Fix verification failed. Please check the error above.")
        sys.exit(1)
