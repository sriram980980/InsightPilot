#!/usr/bin/env python3
"""
Test script to verify the connection dialog fix
"""

import sys
import os
sys.path.append('src')

def test_connection_dialog_fix():
    """Test that the connection dialog doesn't crash with RuntimeError"""
    
    print("Testing connection dialog fix...")
    
    try:
        # Import required modules
        from config.config_manager import ConfigManager
        from ui.dialogs.connection_dialog import ConnectionDialog
        from PySide6.QtWidgets import QApplication
        
        # Create a minimal QApplication (required for Qt widgets)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create config manager
        config_manager = ConfigManager()
        
        # Create dialog
        dialog = ConnectionDialog(config_manager)
        print("✓ ConnectionDialog created successfully")
        
        # Test switching between database types
        print("✓ Testing database type switching...")
        
        dialog.type_combo.setCurrentText("MySQL")
        print("  - Switched to MySQL")
        
        dialog.type_combo.setCurrentText("MongoDB") 
        print("  - Switched to MongoDB")
        
        dialog.type_combo.setCurrentText("PostgreSQL")
        print("  - Switched to PostgreSQL")
        
        dialog.type_combo.setCurrentText("MySQL")
        print("  - Switched back to MySQL")
        
        # Test getting connection config without crashes
        print("✓ Testing get_connection_config()...")
        
        # Fill in some test data
        dialog.name_edit.setText("test-connection")
        dialog.hostname_edit.setText("localhost")
        dialog.username_edit.setText("testuser")
        dialog.password_edit.setText("testpass")
        
        # Test config for each database type
        for db_type in ["MySQL", "MongoDB", "PostgreSQL"]:
            dialog.type_combo.setCurrentText(db_type)
            try:
                config = dialog.get_connection_config()
                print(f"  - {db_type} config retrieved successfully")
                print(f"    Type: {config.get('type')}, Sub-type: {config.get('sub_type')}")
            except RuntimeError as e:
                print(f"  - ❌ {db_type} failed with RuntimeError: {e}")
                return False
            except Exception as e:
                print(f"  - ❌ {db_type} failed with error: {e}")
                return False
        
        print("\n✓ All database type switches completed without RuntimeError!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing connection dialog RuntimeError fix...\n")
    
    success = test_connection_dialog_fix()
    
    if success:
        print("\n" + "="*60)
        print("🎉 CONNECTION DIALOG FIX VERIFIED!")
        print("="*60)
        print("The RuntimeError was caused by:")
        print("  - clear_db_specific_fields() deleting widgets when type changes")
        print("  - get_connection_config() trying to access deleted widgets")
        print("  - Using deleted mysql_schema_edit as fallback for other types")
        print("\nFix applied:")
        print("  ✓ Added proper setup methods for MongoDB and PostgreSQL")
        print("  ✓ Used hasattr() checks before accessing widget attributes")
        print("  ✓ Removed unsafe getattr() calls with deleted widgets")
        print("  ✓ Added safe fallback values for missing configurations")
        print("  ✓ Fixed load_connection_config() to use sub_type properly")
    else:
        print("\n❌ Fix verification failed. Please check the error above.")
        sys.exit(1)
