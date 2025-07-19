"""
Example: How to use InsightPilot with external LLM providers
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.config_manager import ConfigManager
from llm.llm_factory import LLMClientFactory
from llm.enhanced_llm_client import EnhancedLLMClient

def setup_openai_provider(config_manager, api_key):
    """Setup OpenAI provider"""
    print("Setting up OpenAI provider!")
    
    openai_config = LLMClientFactory.get_default_openai_config(api_key, "gpt-4o-mini")
    config_manager.add_llm_provider("openai_main", openai_config)
    
    print("✅ OpenAI provider configured")

def setup_github_copilot_provider(config_manager, github_token):
    """Setup GitHub Copilot provider"""
    print("Setting up GitHub Copilot provider!")
    
    copilot_config = LLMClientFactory.get_default_github_copilot_config(github_token, "gpt-4o")
    config_manager.add_llm_provider("github_copilot", copilot_config)
    
    print("✅ GitHub Copilot provider configured")

def demo_multi_provider_usage():
    """Demonstrate using multiple LLM providers"""
    print("\n" + "="*60)
    print("InsightPilot Multi-Provider Demo")
    print("="*60)
    
    # Initialize config manager
    config_manager = ConfigManager()
    
    # Setup default Ollama provider
    ollama_config = LLMClientFactory.get_default_ollama_config("mistral:7b")
    config_manager.add_llm_provider("local_ollama", ollama_config)
    config_manager.set_default_llm_provider("local_ollama")
    
    # Optionally setup external providers
    # Note: You would need real API keys for these to work
    
    # Uncomment and add your OpenAI API key:
    # setup_openai_provider(config_manager, "your-openai-api-key-here")
    
    # Uncomment and add your GitHub token:
    # setup_github_copilot_provider(config_manager, "your-github-token-here")
    
    # Create enhanced LLM client
    print("\nCreating enhanced LLM client!")
    client = LLMClientFactory.create_from_config(config_manager)
    
    print(f"Available providers: {client.list_providers()}")
    print(f"Current provider: {client.current_provider}")
    
    # Test health of all providers
    print("\nTesting provider health!")
    health_results = client.health_check_all()
    for provider, healthy in health_results.items():
        status = "✅ Healthy" if healthy else "❌ Unhealthy"
        print(f"  {provider}: {status}")
    
    # Demonstrate SQL generation
    print("\n" + "-"*40)
    print("SQL Generation Examples")
    print("-"*40)
    
    schema_info = """
    Tables:
    - users(id, name, email, created_at)
    - orders(id, user_id, amount, order_date)
    - products(id, name, price, category)
    """
    
    # Test questions
    questions = [
        "Find all users who placed orders in the last 30 days",
        "What is the total revenue by product category?",
        "Which users have spent more than $1000 total?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        
        # Use first healthy provider
        healthy_providers = [p for p, h in health_results.items() if h]
        if healthy_providers:
            provider = healthy_providers[0]
            print(f"Using provider: {provider}")
            
            try:
                response = client.generate_sql(schema_info, question, provider)
                
                if response.success:
                    print(f"✅ Generated SQL:")
                    print(f"   {response.content[:100]}!")
                    print(f"   Tokens used: {response.tokens_used}")
                else:
                    print(f"❌ Failed: {response.error}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("⚠️ No healthy providers available")
    
    # Demonstrate fallback capability
    print("\n" + "-"*40)
    print("Fallback Capability Demo")
    print("-"*40)
    
    if len(healthy_providers) > 0:
        print("Testing generation with automatic fallback!")
        
        try:
            response = client.generate_with_fallback(
                "Explain what a database index is in simple terms.",
                fallback_providers=healthy_providers
            )
            
            if response.success:
                print(f"✅ Success with provider: {response.provider}")
                print(f"   Response: {response.content[:100]}!")
            else:
                print(f"❌ All providers failed: {response.error}")
                
        except Exception as e:
            print(f"❌ Error during fallback test: {e}")
    
    # Show provider statistics
    print("\n" + "-"*40)
    print("Provider Statistics")
    print("-"*40)
    
    stats = client.get_provider_stats()
    for provider, stat in stats.items():
        print(f"\n{provider}:")
        print(f"  Type: {stat['provider_type']}")
        print(f"  Model: {stat['model']}")
        print(f"  Healthy: {stat['healthy']}")
        print(f"  Temperature: {stat['config']['temperature']}")
        print(f"  Max Tokens: {stat['config']['max_tokens']}")
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)

def show_configuration_guide():
    """Show how to configure external providers"""
    print("\n" + "="*60)
    print("External LLM Provider Configuration Guide")
    print("="*60)
    
    print("""
1. OpenAI/ChatGPT Setup:
   - Get API key from: https://platform.openai.com/api-keys
   - In InsightPilot UI: Tools → LLM Providers → Add
   - Provider Type: openai
   - Model: gpt-4o-mini (cost-effective) or gpt-4o (most capable)
   - API Key: Your OpenAI API key
   - Base URL: https://api.openai.com/v1

2. GitHub Copilot Setup:
   - Requires GitHub Copilot subscription
   - Get Personal Access Token from: https://github.com/settings/tokens
   - In InsightPilot UI: Tools → LLM Providers → Add
   - Provider Type: github_copilot
   - Model: gpt-4o (recommended)
   - API Key: Your GitHub Personal Access Token
   - Base URL: https://models.inference.ai.azure.com

3. Programmatic Configuration:
   ```python
   from config.config_manager import ConfigManager
   from llm.llm_factory import LLMClientFactory
   
   config_manager = ConfigManager()
   
   # Add OpenAI
   openai_config = LLMClientFactory.get_default_openai_config("your-api-key", "gpt-4o-mini")
   config_manager.add_llm_provider("openai", openai_config)
   
   # Add GitHub Copilot
   copilot_config = LLMClientFactory.get_default_github_copilot_config("your-token", "gpt-4o")
   config_manager.add_llm_provider("copilot", copilot_config)
   
   # Set default
   config_manager.set_default_llm_provider("openai")
   ```

4. Provider Comparison:
   
   Ollama (Local):
   ✅ Free, private, no internet required
   ❌ Limited model selection, requires local resources
   
   OpenAI:
   ✅ Most capable models, fast responses
   ❌ Costs money, requires internet, data sent to OpenAI
   
   GitHub Copilot:
   ✅ Multiple models, good for coding tasks
   ❌ Requires GitHub Copilot subscription, data sent to providers

5. Cost Considerations:
   - OpenAI GPT-4o-mini: ~$0.0002 per query (very affordable)
   - OpenAI GPT-4o: ~$0.005 per query (premium)
   - GitHub Copilot: Included with subscription
   - Ollama: Free (but uses your hardware)
""")

if __name__ == "__main__":
    print("InsightPilot Enhanced LLM Integration")
    print("Choose an option:")
    print("1. Run multi-provider demo")
    print("2. Show configuration guide")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "1":
        demo_multi_provider_usage()
    elif choice == "2":
        show_configuration_guide()
    else:
        print("Running demo by default!")
        demo_multi_provider_usage()
