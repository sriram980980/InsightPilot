"""
LLM Client Factory for creating configured LLM clients
"""

import logging
from typing import Dict, Any, Optional

from .enhanced_llm_client import EnhancedLLMClient
from .providers.base_provider import LLMConfig


class LLMClientFactory:
    """Factory for creating configured LLM clients"""
    
    @staticmethod
    def create_from_config(config_manager) -> EnhancedLLMClient:
        """Create an enhanced LLM client from configuration"""
        logger = logging.getLogger(__name__)
        
        # Get provider configurations
        provider_configs = config_manager.get_llm_providers()
        llm_settings = config_manager.get_llm_settings()
        default_provider = llm_settings.get("default_provider", "ollama")
        
        # Convert config format to LLMConfig objects
        llm_configs = {}
        for name, config in provider_configs.items():
            if config.get("enabled", True):
                try:
                    llm_config = LLMConfig(
                        provider=config["provider"],
                        model=config["model"],
                        api_key=config.get("api_key"),
                        base_url=config.get("base_url"),
                        temperature=config.get("temperature", 0.1),
                        max_tokens=config.get("max_tokens", 1000),
                        timeout=config.get("timeout", 180),
                        additional_params=config.get("additional_params")
                    )
                    llm_configs[name] = llm_config
                    logger.info(f"Configured LLM provider: {name}")
                except Exception as e:
                    logger.error(f"Failed to configure provider {name}: {e}")
        
        # Create enhanced client
        if llm_configs:
            return EnhancedLLMClient(llm_configs, default_provider)
        else:
            # Fallback to default Ollama configuration
            logger.warning("No providers configured, using default Ollama setup")
            default_config = LLMConfig(
                provider="ollama",
                model="mistral:7b",
                base_url="http://localhost:11434",
                temperature=0.1,
                max_tokens=1000,
                timeout=180
            )
            return EnhancedLLMClient({"ollama": default_config}, "ollama")
    
    @staticmethod
    def create_provider_config(
        provider: str,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a provider configuration dictionary"""
        config = {
            "provider": provider,
            "model": model,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "timeout": kwargs.get("timeout", 180),
            "enabled": kwargs.get("enabled", True)
        }
        
        if api_key:
            config["api_key"] = api_key
        if base_url:
            config["base_url"] = base_url
        if kwargs.get("additional_params"):
            config["additional_params"] = kwargs["additional_params"]
        
        return config
    
    @staticmethod
    def get_default_openai_config(api_key: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """Get default OpenAI provider configuration"""
        return LLMClientFactory.create_provider_config(
            provider="openai",
            model=model,
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            temperature=0.1,
            max_tokens=1000,
            timeout=180
        )
    
    @staticmethod
    def get_default_github_copilot_config(token: str, model: str = "gpt-4o") -> Dict[str, Any]:
        """Get default GitHub Copilot provider configuration"""
        return LLMClientFactory.create_provider_config(
            provider="github_copilot",
            model=model,
            api_key=token,
            base_url="https://models.inference.ai.azure.com",
            temperature=0.1,
            max_tokens=1000,
            timeout=180
        )
    
    @staticmethod
    def get_default_ollama_config(model: str = "mistral:7b", host: str = "localhost", port: int = 11434) -> Dict[str, Any]:
        """Get default Ollama provider configuration"""
        return LLMClientFactory.create_provider_config(
            provider="ollama",
            model=model,
            base_url=f"http://{host}:{port}",
            temperature=0.1,
            max_tokens=1000,
            timeout=180
        )
