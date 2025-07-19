#!/usr/bin/env python3
"""
Test script for LLM integration in InsightPilot
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_llm_dialog():
    """Test LLM connection dialog"""
    print("Testing LLM Connection Dialog!")
    
    try:
        from PySide6.QtWidgets import QApplication
        from config.config_manager import ConfigManager
        from ui.dialogs.llm_connection_dialog import LLMConnectionDialog
        
        app = QApplication(sys.argv)
        config_manager = ConfigManager()
        
        # Test dialog creation
        dialog = LLMConnectionDialog(config_manager)
        print("✓ LLM Connection Dialog created successfully")
        
        # Test form fields
        assert hasattr(dialog, 'name_edit'), "Name field missing"
        assert hasattr(dialog, 'host_edit'), "Host field missing"
        assert hasattr(dialog, 'port_spin'), "Port field missing"
        assert hasattr(dialog, 'model_combo'), "Model field missing"
        print("✓ All form fields present")
        
        # Test default values
        assert dialog.host_edit.text() == "localhost", "Default host incorrect"
        assert dialog.port_spin.value() == 11434, "Default port incorrect"
        print("✓ Default values set correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_llm_service():
    """Test LLM service functionality"""
    print("\nTesting LLM Service!")
    
    try:
        from llm.llm_service import LLMService
        
        service = LLMService()
        print("✓ LLM Service created successfully")
        
        # Test Ollama installation check
        installed, version = service.check_ollama_installation()
        if installed:
            print(f"✓ Ollama installed: {version}")
        else:
            print(f"⚠ Ollama not installed: {version}")
        
        # Test status check
        status = service.get_status()
        print(f"✓ LLM Status: Running={status['running']}, Models={len(status['models'])}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_config_manager():
    """Test config manager LLM support"""
    print("\nTesting Config Manager LLM Support!")
    
    try:
        from config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        print("✓ Config Manager created successfully")
        
        # Test saving LLM connection
        llm_config = {
            'type': 'LLM',
            'host': 'localhost',
            'port': 11434,
            'model': 'mistral:7b',
            'temperature': 0.1,
            'max_tokens': 1000
        }
        
        config_manager.save_connection("Test LLM", llm_config)
        print("✓ LLM connection saved")
        
        # Test retrieving connections
        connections = config_manager.get_connections()
        assert "Test LLM" in connections, "LLM connection not found"
        assert connections["Test LLM"]["type"] == "LLM", "LLM connection type incorrect"
        print("✓ LLM connection retrieved correctly")
        
        # Clean up
        config_manager.remove_connection("Test LLM")
        print("✓ LLM connection removed")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_connections_tab():
    """Test connections tab integration"""
    print("\nTesting Connections Tab Integration!")
    
    try:
        from PySide6.QtWidgets import QApplication
        from config.config_manager import ConfigManager
        from ui.tabs.connections_tab import ConnectionsTab
        
        app = QApplication(sys.argv)
        config_manager = ConfigManager()
        
        # Test tab creation
        tab = ConnectionsTab(config_manager)
        print("✓ Connections Tab created successfully")
        
        # Test LLM controls
        assert hasattr(tab, 'start_llm_btn'), "Start LLM button missing"
        assert hasattr(tab, 'stop_llm_btn'), "Stop LLM button missing"
        assert hasattr(tab, 'llm_status_label'), "LLM status label missing"
        assert hasattr(tab, 'new_llm_btn'), "New LLM button missing"
        print("✓ All LLM controls present")
        
        # Test filter combo
        assert hasattr(tab, 'connection_filter'), "Connection filter missing"
        filter_items = [tab.connection_filter.itemText(i) for i in range(tab.connection_filter.count())]
        assert "LLM" in filter_items, "LLM filter option missing"
        print("✓ LLM filter option available")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("InsightPilot LLM Integration Test")
    print("=" * 40)
    
    # Set up logging
    logging.basicConfig(level=logging.ERROR)  # Suppress non-error logs
    
    tests = [
        ("LLM Service", test_llm_service),
        ("Config Manager", test_config_manager),
        ("LLM Dialog", test_llm_dialog),
        ("Connections Tab", test_connections_tab),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Summary:")
    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n✓ All tests passed!")
        print("  LLM integration is ready for use")
        print("\nNext steps:")
        print("  1. Install Ollama: https://ollama.ai/")
        print("  2. Run: ollama pull mistral:7b")
        print("  3. Start InsightPilot and use the LLM controls")
    else:
        print(f"\n✗ {len(results) - passed} tests failed")
        print("  Please check the error messages above")
    
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
