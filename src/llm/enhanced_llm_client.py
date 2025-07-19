"""
Enhanced LLM Client with support for multiple providers
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from .providers.base_provider import BaseLLMProvider, LLMResponse, LLMConfig
from .providers.ollama_provider import OllamaProvider
from .providers.openai_provider import OpenAIProvider
from .providers.github_copilot_provider import GitHubCopilotProvider


class LLMProviderType(Enum):
    """Supported LLM provider types"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    GITHUB_COPILOT = "github_copilot"


class EnhancedLLMClient:
    """Enhanced LLM client supporting multiple providers"""
    
    def __init__(self, provider_configs: Dict[str, LLMConfig], default_provider: str = "ollama"):
        self.logger = logging.getLogger(__name__)
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider = default_provider
        self.current_provider = default_provider
        
        # Initialize providers
        for provider_name, config in provider_configs.items():
            try:
                provider = self._create_provider(config)
                self.providers[provider_name] = provider
                self.logger.info(f"Initialized {provider_name} provider")
            except Exception as e:
                self.logger.error(f"Failed to initialize {provider_name} provider: {e}")
    
    def _create_provider(self, config: LLMConfig) -> BaseLLMProvider:
        """Create a provider instance based on config"""
        provider_type = LLMProviderType(config.provider)
        
        if provider_type == LLMProviderType.OLLAMA:
            return OllamaProvider(config)
        elif provider_type == LLMProviderType.OPENAI:
            return OpenAIProvider(config)
        elif provider_type == LLMProviderType.GITHUB_COPILOT:
            return GitHubCopilotProvider(config)
        else:
            raise ValueError(f"Unsupported provider type: {config.provider}")
    
    def add_provider(self, name: str, config: LLMConfig) -> bool:
        """Add a new provider"""
        try:
            provider = self._create_provider(config)
            self.providers[name] = provider
            self.logger.info(f"Added provider: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add provider {name}: {e}")
            return False
    
    def remove_provider(self, name: str) -> bool:
        """Remove a provider"""
        if name in self.providers:
            del self.providers[name]
            if self.current_provider == name:
                self.current_provider = self.default_provider
            self.logger.info(f"Removed provider: {name}")
            return True
        return False
    
    def set_current_provider(self, provider_name: str) -> bool:
        """Set the current active provider"""
        if provider_name in self.providers:
            self.current_provider = provider_name
            self.logger.info(f"Switched to provider: {provider_name}")
            return True
        else:
            self.logger.error(f"Provider {provider_name} not found")
            return False
    
    def get_current_provider(self) -> Optional[BaseLLMProvider]:
        """Get the current active provider"""
        return self.providers.get(self.current_provider)
    
    def get_provider(self, provider_name: str) -> Optional[BaseLLMProvider]:
        """Get a specific provider by name"""
        return self.providers.get(provider_name)
    
    def list_providers(self) -> List[str]:
        """List all available provider names"""
        return list(self.providers.keys())
    
    def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers"""
        results = {}
        for name, provider in self.providers.items():
            results[name] = provider.health_check()
        return results
    
    def health_check(self, provider_name: str = None) -> bool:
        """Check health of current or specified provider"""
        provider = self.get_provider(provider_name) if provider_name else self.get_current_provider()
        if provider:
            return provider.health_check()
        return False
    
    def generate(self, prompt: str, provider_name: str = None, **kwargs) -> LLMResponse:
        """Generate text using current or specified provider"""
        provider = self.get_provider(provider_name) if provider_name else self.get_current_provider()
        
        if not provider:
            error_msg = f"Provider {provider_name or self.current_provider} not available"
            self.logger.error(error_msg)
            return LLMResponse(
                content="",
                success=False,
                error=error_msg
            )
        
        return provider.generate(prompt, **kwargs)
    
    def generate_with_fallback(self, prompt: str, fallback_providers: List[str] = None, **kwargs) -> LLMResponse:
        """Generate text with automatic fallback to other providers"""
        # Try current provider first
        result = self.generate(prompt, **kwargs)
        if result.success:
            return result
        
        # Try fallback providers
        fallback_list = fallback_providers or [name for name in self.providers.keys() if name != self.current_provider]
        
        for provider_name in fallback_list:
            self.logger.info(f"Trying fallback provider: {provider_name}")
            result = self.generate(prompt, provider_name, **kwargs)
            if result.success:
                return result
        
        # All providers failed
        return LLMResponse(
            content="",
            success=False,
            error="All providers failed to generate response"
        )
    
    def generate_sql(self, schema_info: str, question: str, provider_name: str = None) -> LLMResponse:
        """Generate SQL query from schema and question"""
        provider = self.get_provider(provider_name) if provider_name else self.get_current_provider()
        
        if not provider:
            error_msg = f"Provider {provider_name or self.current_provider} not available"
            return LLMResponse(content="", success=False, error=error_msg)
        
        return provider.generate_sql(schema_info, question)
    
    def generate_sql_custom_prompt(self, custom_prompt: str, provider_name: str = None) -> LLMResponse:
        """Generate SQL query using a custom prompt"""
        provider = self.get_provider(provider_name) if provider_name else self.get_current_provider()
        
        if not provider:
            error_msg = f"Provider {provider_name or self.current_provider} not available"
            return LLMResponse(content="", success=False, error=error_msg)
        
        return provider.generate_sql_custom_prompt(custom_prompt)
    
    def generate_mongodb_query(self, schema_info: str, question: str, provider_name: str = None) -> LLMResponse:
        """Generate MongoDB aggregation query"""
        provider = self.get_provider(provider_name) if provider_name else self.get_current_provider()
        
        if not provider:
            error_msg = f"Provider {provider_name or self.current_provider} not available"
            return LLMResponse(content="", success=False, error=error_msg)
        
        return provider.generate_mongodb_query(schema_info, question)
    
    def recommend_chart(self, columns: List[str], sample_data: List[List[Any]], question: str, user_hint: str = "", provider_name: str = None) -> LLMResponse:
        """Ask LLM to recommend the best chart type"""
        provider = self.get_provider(provider_name) if provider_name else self.get_current_provider()
        
        if not provider:
            error_msg = f"Provider {provider_name or self.current_provider} not available"
            return LLMResponse(content="", success=False, error=error_msg)
        
        return provider.recommend_chart(columns, sample_data, question, user_hint)
    
    def explain_query(self, query: str, provider_name: str = None) -> LLMResponse:
        """Ask LLM to explain the generated query"""
        provider = self.get_provider(provider_name) if provider_name else self.get_current_provider()
        
        if not provider:
            error_msg = f"Provider {provider_name or self.current_provider} not available"
            return LLMResponse(content="", success=False, error=error_msg)
        
        return provider.explain_query(query)
    
    def list_models(self, provider_name: str = None) -> Dict[str, Any]:
        """List available models for current or specified provider"""
        provider = self.get_provider(provider_name) if provider_name else self.get_current_provider()
        
        if not provider:
            return {"models": []}
        
        return provider.list_models()
    
    def update_model(self, model_name: str, provider_name: str = None) -> bool:
        """Update model for current or specified provider"""
        provider = self.get_provider(provider_name) if provider_name else self.get_current_provider()
        
        if not provider:
            return False
        
        return provider.update_model(model_name)
    
    def update_parameters(self, provider_name: str = None, **params) -> bool:
        """Update generation parameters for current or specified provider"""
        provider = self.get_provider(provider_name) if provider_name else self.get_current_provider()
        
        if not provider:
            return False
        
        provider.update_parameters(**params)
        return True
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers"""
        stats = {}
        for name, provider in self.providers.items():
            stats[name] = {
                "provider_type": provider.config.provider,
                "model": provider.config.model,
                "healthy": provider.health_check(),
                "config": {
                    "temperature": provider.config.temperature,
                    "max_tokens": provider.config.max_tokens,
                    "timeout": provider.config.timeout
                }
            }
        return stats
