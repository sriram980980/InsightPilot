# Enhanced LLM Integration Guide

InsightPilot now supports multiple LLM providers including Ollama (local), OpenAI/ChatGPT, and GitHub Copilot. This guide explains how to configure and use these providers.

## Supported Providers

### 1. Ollama (Local LLMs)
- **Provider Type**: `ollama`
- **Requirements**: Ollama installed locally
- **Models**: Any model available in Ollama (mistral:7b, llama2:7b, codellama:7b, etc.)
- **Configuration**: Host and port for Ollama server

### 2. OpenAI/ChatGPT
- **Provider Type**: `openai`
- **Requirements**: OpenAI API key
- **Models**: gpt-4, gpt-4-turbo, gpt-4o, gpt-4o-mini, gpt-3.5-turbo, etc.
- **Configuration**: API key required

### 3. GitHub Copilot
- **Provider Type**: `github_copilot`
- **Requirements**: GitHub Personal Access Token with Copilot access
- **Models**: gpt-4o, gpt-4o-mini, claude-3.5-sonnet, o1-preview, o1-mini
- **Configuration**: GitHub PAT required

## Configuration

### Using the UI

1. **Open Connection Management**
   - Go to the `Connections` tab
   - Click "Add Connection" button
   - Select "LLM" as the connection type

2. **Add an LLM Provider**
   - Click "Add Connection" in the connections tab
   - Enter a name for your LLM connection
   - Configure the provider settings:
     - **Provider Type**: Select from ollama, openai, or github_copilot
     - **Model**: Specify the model name
     - **API Key**: Enter your API key (for OpenAI/GitHub Copilot)
     - **Base URL**: Custom endpoint URL (optional)
     - **Generation Parameters**: Temperature, max tokens, timeout

3. **Test Connection**
   - Click "Test Connection" to verify the provider works
   - Check the status indicator for success/failure

4. **Set Default Provider**
   - Choose your preferred default provider from the dropdown
   - This will be used when no specific provider is selected

5. **Save Configuration**
   - Click "Save" to apply all changes

### Programmatic Configuration

```python
from config.config_manager import ConfigManager
from llm.llm_factory import LLMClientFactory

config_manager = ConfigManager()

# Add Ollama provider
ollama_config = LLMClientFactory.get_default_ollama_config("mistral:7b")
config_manager.add_llm_provider("local_ollama", ollama_config)

# Add OpenAI provider
openai_config = LLMClientFactory.get_default_openai_config("your-api-key", "gpt-4o-mini")
config_manager.add_llm_provider("openai_gpt4", openai_config)

# Add GitHub Copilot provider
copilot_config = LLMClientFactory.get_default_github_copilot_config("your-github-token", "gpt-4o")
config_manager.add_llm_provider("github_copilot", copilot_config)

# Set default provider
config_manager.set_default_llm_provider("local_ollama")
```

## Using Multiple Providers

### Enhanced LLM Client

The `EnhancedLLMClient` provides a unified interface for all providers:

```python
from llm.llm_factory import LLMClientFactory

# Create client from configuration
client = LLMClientFactory.create_from_config(config_manager)

# List available providers
providers = client.list_providers()
print(f"Available providers: {providers}")

# Use default provider
response = client.generate("Explain SQL joins in simple terms")

# Use specific provider
response = client.generate("Write a SQL query", provider_name="openai_gpt4")

# Generate with fallback
response = client.generate_with_fallback(
    "Complex data analysis query",
    fallback_providers=["openai_gpt4", "local_ollama"]
)
```

### Provider-Specific Features

#### OpenAI Provider
- Automatic cost estimation based on token usage
- Support for all GPT models including GPT-4o and GPT-3.5
- Structured chat completion format

#### GitHub Copilot Provider
- Access to multiple models (GPT-4o, Claude, o1-preview)
- Rate limit monitoring
- GitHub token validation

#### Ollama Provider
- Model management (pull, list, info)
- Local model execution
- No API costs

## SQL Generation Examples

### Basic SQL Generation
```python
# Generate SQL query
response = client.generate_sql(
    schema_info="Tables: users(id, name, email), orders(id, user_id, amount)",
    question="Find users who spent more than $1000 total"
)

if response.success:
    print(f"Generated SQL: {response.content}")
    print(f"Used provider: {response.provider}")
```

### Provider-Specific SQL Generation
```python
# Use OpenAI for complex queries
complex_response = client.generate_sql(
    schema_info=schema_info,
    question="Complex analytical query with window functions",
    provider_name="openai_gpt4"
)

# Use Ollama for simple queries
simple_response = client.generate_sql(
    schema_info=schema_info,
    question="Simple select query",
    provider_name="local_ollama"
)
```

## Best Practices

### Provider Selection
1. **Ollama** - Best for privacy, no API costs, good for simple queries
2. **OpenAI** - Best for complex queries, excellent reasoning, costs apply
3. **GitHub Copilot** - Good balance, multiple models, requires GitHub subscription

### Error Handling
```python
# The client provides automatic fallback
response = client.generate_with_fallback(prompt, ["primary", "fallback1", "fallback2"])

if not response.success:
    print(f"All providers failed: {response.error}")
```

### Performance Optimization
- Use appropriate models for the task complexity
- Set reasonable timeout values
- Monitor token usage for cost-sensitive operations
- Cache common queries when possible

## Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   - Ensure Ollama is running: `ollama serve`
   - Check if the model is available: `ollama list`
   - Verify the base URL (default: http://localhost:11434)

2. **OpenAI API Errors**
   - Verify API key is valid and has sufficient credits
   - Check model availability for your account
   - Ensure proper internet connectivity

3. **GitHub Copilot Access Denied**
   - Verify you have a GitHub Copilot subscription
   - Check that your Personal Access Token has appropriate scopes
   - Ensure token hasn't expired

### Configuration Issues

1. **Provider Not Listed**
   - Check that the provider is enabled in configuration
   - Verify the provider type spelling
   - Restart the application after configuration changes

2. **Model Not Found**
   - For Ollama: Pull the model first: `ollama pull model-name`
   - For OpenAI: Check model availability in your account
   - For GitHub Copilot: Verify model is supported

## Security Considerations

- API keys are stored securely using system keyring
- Configuration files are encrypted at rest
- Local Ollama provides complete privacy (no data sent externally)
- Always use environment variables or secure storage for API keys in production

## Cost Management

### OpenAI Pricing (approximate)
- GPT-4o: $0.005 per 1K input tokens, $0.015 per 1K output tokens
- GPT-4o-mini: $0.00015 per 1K input tokens, $0.0006 per 1K output tokens
- GPT-3.5-turbo: $0.0015 per 1K input tokens, $0.002 per 1K output tokens

### Cost Optimization Tips
1. Use smaller models for simple queries
2. Set appropriate max_tokens limits
3. Monitor token usage with the built-in cost estimation
4. Use Ollama for development and testing
5. Cache responses when appropriate

## Integration with InsightPilot Features

The enhanced LLM integration works seamlessly with:
- **Query Chat Tab**: Natural language to SQL conversion
- **Results Visualization**: Chart type recommendations
- **Query Explanation**: Detailed SQL explanations
- **Error Handling**: Improved error suggestions and retry logic
- **History Management**: Track which provider was used for each query

## Future Enhancements

Planned improvements include:
- Support for additional providers (Anthropic Claude, Google Gemini)
- Advanced prompt engineering templates
- Provider performance analytics
- Automatic model selection based on query complexity
- Streaming responses for long generations
