#!/usr/bin/env python3
"""
Test script for the new connection type and sub-type system
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.config_manager import ConfigManager

def test_connection_types():
    """Test the new connection type system"""
    print("Testing Connection Types and Sub-Types")
    print("=" * 50)
    
    # Create config manager
    config_manager = ConfigManager()
    
    # Test LLM connections
    print("\n1. Testing LLM Connections:")
    
    # GitHub Copilot connection
    github_config = {
        "type": "LLM",
        "sub_type": "github",
        "model": "gpt-4o",
        "token": "test_token",
        "base_url": "https://models.inference.ai.azure.com",
        "enabled": True
    }
    
    try:
        config_manager.save_connection("test_github", github_config)
        print("✓ GitHub LLM connection saved successfully")
        
        # Test provider class resolution
        provider_class = config_manager.get_provider_class_name("test_github")
        module_path = config_manager.get_provider_module_path("test_github")
        print(f"  Provider class: {provider_class}")
        print(f"  Module path: {module_path}")
        
    except Exception as e:
        print(f"✗ GitHub LLM connection failed: {e}")
    
    # OpenAI connection
    openai_config = {
        "type": "LLM", 
        "sub_type": "openai",
        "model": "gpt-4",
        "api_key": "test_api_key",
        "base_url": "https://api.openai.com/v1",
        "enabled": True
    }
    
    try:
        config_manager.save_connection("test_openai", openai_config)
        print("✓ OpenAI LLM connection saved successfully")
        
        provider_class = config_manager.get_provider_class_name("test_openai")
        module_path = config_manager.get_provider_module_path("test_openai")
        print(f"  Provider class: {provider_class}")
        print(f"  Module path: {module_path}")
        
    except Exception as e:
        print(f"✗ OpenAI LLM connection failed: {e}")
    
    # Ollama connection
    ollama_config = {
        "type": "LLM",
        "sub_type": "ollama", 
        "model": "mistral:7b",
        "host": "localhost",
        "port": 11434,
        "enabled": True
    }
    
    try:
        config_manager.save_connection("test_ollama", ollama_config)
        print("✓ Ollama LLM connection saved successfully")
        
        provider_class = config_manager.get_provider_class_name("test_ollama")
        module_path = config_manager.get_provider_module_path("test_ollama")
        print(f"  Provider class: {provider_class}")
        print(f"  Module path: {module_path}")
        
    except Exception as e:
        print(f"✗ Ollama LLM connection failed: {e}")
    
    # Test Database connections
    print("\n2. Testing Database Connections:")
    
    # MySQL connection
    mysql_config = {
        "type": "DB",
        "sub_type": "mysql",
        "host": "localhost",
        "port": 3306,
        "database": "test_db",
        "username": "test_user",
        "password": "test_pass"
    }
    
    try:
        config_manager.save_connection("test_mysql", mysql_config)
        print("✓ MySQL DB connection saved successfully")
        
        adapter_class = config_manager.get_provider_class_name("test_mysql")
        module_path = config_manager.get_provider_module_path("test_mysql")
        print(f"  Adapter class: {adapter_class}")
        print(f"  Module path: {module_path}")
        
    except Exception as e:
        print(f"✗ MySQL DB connection failed: {e}")
    
    # MongoDB connection
    mongo_config = {
        "type": "DB",
        "sub_type": "mongodb",
        "host": "localhost", 
        "port": 27017,
        "database": "test_db",
        "username": "test_user",
        "password": "test_pass"
    }
    
    try:
        config_manager.save_connection("test_mongo", mongo_config)
        print("✓ MongoDB DB connection saved successfully")
        
        adapter_class = config_manager.get_provider_class_name("test_mongo")
        module_path = config_manager.get_provider_module_path("test_mongo")
        print(f"  Adapter class: {adapter_class}")
        print(f"  Module path: {module_path}")
        
    except Exception as e:
        print(f"✗ MongoDB DB connection failed: {e}")
    
    # Test invalid sub-types
    print("\n3. Testing Invalid Sub-Types:")
    
    invalid_llm_config = {
        "type": "LLM",
        "sub_type": "invalid_llm",
        "model": "test"
    }
    
    try:
        config_manager.save_connection("test_invalid_llm", invalid_llm_config)
        print("✗ Invalid LLM sub-type should have failed")
    except ValueError as e:
        print(f"✓ Invalid LLM sub-type correctly rejected: {e}")
    
    invalid_db_config = {
        "type": "DB", 
        "sub_type": "invalid_db",
        "host": "localhost"
    }
    
    try:
        config_manager.save_connection("test_invalid_db", invalid_db_config)
        print("✗ Invalid DB sub-type should have failed")
    except ValueError as e:
        print(f"✓ Invalid DB sub-type correctly rejected: {e}")
    
    # Display final connection state
    print("\n4. Final Connection Summary:")
    llm_connections = config_manager.get_llm_connections()
    db_connections = config_manager.get_database_connections()
    
    print(f"LLM Connections: {len(llm_connections)}")
    for name, config in llm_connections.items():
        print(f"  {name}: {config.get('sub_type', 'unknown')}")
    
    print(f"DB Connections: {len(db_connections)}")
    for name, config in db_connections.items():
        if hasattr(config, 'get'):
            print(f"  {name}: {config.get('sub_type', 'unknown')}")
        else:
            print(f"  {name}: legacy format")

if __name__ == "__main__":
    test_connection_types()
