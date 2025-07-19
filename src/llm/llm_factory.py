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
        
        # Get LLM connections instead of providers
        llm_connections = config_manager.get_llm_connections()
        default_provider = config_manager.get_default_llm_connection()
        
        # Convert LLM connections to LLMConfig objects using sub_type
        llm_configs = {}
        for name, connection_config in llm_connections.items():
            if connection_config.get("type", "").upper() == "LLM":
                try:
                    # Use sub_type instead of provider_type for consistent mapping
                    sub_type = connection_config.get("sub_type", "").lower()
                    
                    # Map sub_type to provider names for LLMConfig
                    provider_type_map = {
                        "openai": "openai",
                        "github": "github_copilot", 
                        "ollama": "ollama"
                    }
                    
                    provider_type = provider_type_map.get(sub_type)
                    if not provider_type:
                        logger.warning(f"Unknown LLM sub_type '{sub_type}' for connection '{name}', skipping")
                        continue
                    
                    llm_config = LLMConfig(
                        provider=provider_type,
                        model=connection_config.get("model", "mistral:7b"),
                        api_key=connection_config.get("token") or connection_config.get("api_key"),
                        base_url=connection_config.get("base_url"),
                        temperature=connection_config.get("temperature", 0.1),
                        max_tokens=connection_config.get("max_tokens", 1000),
                        timeout=connection_config.get("timeout", 180),
                        additional_params=connection_config.get("additional_params")
                    )
                    
                    # Handle Ollama connections that might not have explicit base_url
                    if sub_type == "ollama" and not llm_config.base_url:
                        host = connection_config.get("host", "localhost")
                        port = connection_config.get("port", 11434)
                        llm_config.base_url = f"http://{host}:{port}"
                    
                    llm_configs[name] = llm_config
                    logger.info(f"Configured LLM connection: {name} (sub_type: {sub_type} -> provider: {provider_type})")
                    
                except Exception as e:
                    logger.error(f"Failed to configure connection {name}: {e}")
        
        # Create enhanced client
        if llm_configs:
            return EnhancedLLMClient(llm_configs, default_provider)
        else:
            # If no connections exist, return empty client
            logger.warning("No LLM connections configured")
            return EnhancedLLMClient({}, None)
    
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
