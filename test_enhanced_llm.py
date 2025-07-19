"""
Test script for enhanced LLM client with multiple providers
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llm.llm_factory import LLMClientFactory
from llm.enhanced_llm_client import EnhancedLLMClient
from config.config_manager import ConfigManager

def test_enhanced_llm_client():
    """Test the enhanced LLM client with multiple providers"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Testing Enhanced LLM Client!")
    
    # Initialize config manager
    config_manager = ConfigManager()
    
    # Add sample provider configurations
    logger.info("Adding sample provider configurations!")
    
    # Add Ollama provider (should work if Ollama is running)
    ollama_config = LLMClientFactory.get_default_ollama_config("mistral:7b")
    config_manager.add_llm_provider("ollama", ollama_config)
    
    # Set default provider
    config_manager.set_default_llm_provider("ollama")
    
    logger.info("Provider configurations added")
    
    # Create enhanced LLM client
    logger.info("Creating enhanced LLM client!")
    client = LLMClientFactory.create_from_config(config_manager)
    
    # Test provider listing
    logger.info(f"Available providers: {client.list_providers()}")
    logger.info(f"Current provider: {client.current_provider}")
    
    # Test health checks
    logger.info("Testing provider health checks!")
    health_results = client.health_check_all()
    for provider, healthy in health_results.items():
        status = "✅ Healthy" if healthy else "❌ Unhealthy"
        logger.info(f"Provider {provider}: {status}")
    
    # Test simple generation (only if a provider is healthy)
    healthy_providers = [p for p, h in health_results.items() if h]
    if healthy_providers:
        test_provider = healthy_providers[0]
        logger.info(f"Testing text generation with {test_provider}!")
        
        try:
            response = client.generate(
                "Explain what SQL is in one sentence.",
                provider_name=test_provider
            )
            
            if response.success:
                logger.info(f"✅ Generation successful: {response.content[:100]}!")
                logger.info(f"Model: {response.model}, Tokens: {response.tokens_used}, Provider: {response.provider}")
            else:
                logger.error(f"❌ Generation failed: {response.error}")
                
        except Exception as e:
            logger.error(f"❌ Generation error: {e}")
    else:
        logger.warning("⚠️ No healthy providers available for testing")
    
    # Test provider statistics
    logger.info("Provider statistics:")
    stats = client.get_provider_stats()
    for provider, stat in stats.items():
        logger.info(f"  {provider}: {stat}")
    
    logger.info("Enhanced LLM client test completed!")

def test_provider_configurations():
    """Test different provider configurations"""
    logger = logging.getLogger(__name__)
    
    logger.info("Testing provider configuration templates!")
    
    # Test Ollama config
    ollama_config = LLMClientFactory.get_default_ollama_config("llama2:7b")
    logger.info(f"Ollama config: {ollama_config}")
    
    # Test OpenAI config (with dummy key)
    try:
        openai_config = LLMClientFactory.get_default_openai_config("dummy-key", "gpt-4o-mini")
        logger.info(f"OpenAI config: {openai_config}")
    except Exception as e:
        logger.info(f"OpenAI config (expected to need API key): {e}")
    
    # Test GitHub Copilot config (with dummy token)
    try:
        copilot_config = LLMClientFactory.get_default_github_copilot_config("dummy-token", "gpt-4o")
        logger.info(f"GitHub Copilot config: {copilot_config}")
    except Exception as e:
        logger.info(f"GitHub Copilot config (expected to need token): {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("InsightPilot Enhanced LLM Client Test")
    print("=" * 60)
    
    test_provider_configurations()
    print()
    test_enhanced_llm_client()
    
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)
