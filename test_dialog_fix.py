#!/usr/bin/env python3
"""
Test script to verify the LLM dialog fix
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QDialog
from src.ui.dialogs.llm_connection_dialog import LLMConnectionDialog
from src.config.config_manager import ConfigManager

def test_dialog_constants():
    """Test that QDialog.Accepted is accessible"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        # Test that QDialog.Accepted is accessible
        accepted_value = QDialog.Accepted
        rejected_value = QDialog.Rejected
        
        print(f"✅ QDialog.Accepted = {accepted_value}")
        print(f"✅ QDialog.Rejected = {rejected_value}")
        
        # Test creating the dialog
        config_manager = ConfigManager()
        dialog = LLMConnectionDialog(config_manager)
        
        print("✅ LLMConnectionDialog created successfully")
        print("✅ Dialog fix verification complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if app:
            app.quit()

if __name__ == "__main__":
    success = test_dialog_constants()
    sys.exit(0 if success else 1)
