#!/usr/bin/env python3
"""
Fix GitHub provider configuration issue
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.config_manager import ConfigManager

def main():
    """Fix the GitHub provider configuration"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("InsightPilot GitHub Provider Configuration Fix")
    print("=" * 50)
    
    try:
        # Initialize config manager
        config_manager = ConfigManager()
        
        # Show current LLM providers
    except Exception as e:
        print(f"❌ Error fixing configuration: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
