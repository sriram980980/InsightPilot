"""
LLM client for Ollama integration and multi-provider support
"""

import json
import logging
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Import enhanced client components
from .providers.base_provider import LLMResponse
from .enhanced_llm_client import EnhancedLLMClient
from .llm_factory import LLMClientFactory


class LLMClient:
    """Legacy LLM client for backward compatibility"""
    
    def __init__(self, host: str = "localhost", port: int = 11434, model: str = "mistral:7b"):
        self.host = host
        self.port = port
        self.model = model
        self.base_url = f"http://{host}:{port}"
        self.logger = logging.getLogger(__name__)
        
        # Default generation parameters
        self.default_params = {
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": 1000,
            "stop": ["</s>", "###"]
        }
    
    def generate_sql(self, schema_info: str, question: str) -> LLMResponse:
        """Generate SQL query from schema and question using LLM"""
        from .prompt_builder import PromptBuilder
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_sql_prompt(schema_info, question)
        return self.generate(prompt)

    def generate_sql_custom_prompt(self, custom_prompt: str) -> LLMResponse:
        """Generate SQL query using a custom prompt (for retry scenarios)"""
        return self.generate(custom_prompt)

    def generate_mongodb_query(self, schema_info: str, question: str) -> LLMResponse:
        """Generate MongoDB aggregation query from schema and question using LLM"""
        from .prompt_builder import PromptBuilder
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_mongodb_prompt(schema_info, question)
        return self.generate(prompt)

    def recommend_chart(self, columns: List[str], sample_data: List[List[Any]], question: str, user_hint: str = "") -> LLMResponse:
        """Ask LLM to recommend the best chart type for the data"""
        from .prompt_builder import PromptBuilder
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_chart_recommendation_prompt(columns, sample_data, question, user_hint)
        return self.generate(prompt)

    def explain_query(self, query: str) -> LLMResponse:
        """Ask LLM to explain the generated query"""
        from .prompt_builder import PromptBuilder
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_explain_prompt(query)
        return self.generate(prompt)
        from .prompt_builder import PromptBuilder
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_explain_prompt(query)
        return self.generate(prompt)
    
    # Ollama-specific implementation methods
    def health_check(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Ollama health check failed: {e}")
            return False
    
    def list_models(self) -> Dict[str, Any]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to list models: {e}")
            return {"models": []}
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry"""
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=300  # 5 minutes timeout for model download
            )
            return response.status_code == 200
        except requests.RequestException as e:
            self.logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using the LLM"""
        try:
            # Merge default params with provided kwargs
            params = {**self.default_params, **kwargs}
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": params.get("temperature", 0.1),
                    "top_p": params.get("top_p", 0.9),
                    "num_predict": params.get("max_tokens", 1000)
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=180  # Increased timeout for long LLM generations
            )
            response.raise_for_status()
            
            data = response.json()
            return LLMResponse(
                content=data.get("response", ""),
                success=True,
                model=data.get("model"),
                tokens_used=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                provider="ollama"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate text: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=str(e),
                provider="ollama"
            )
    
    def update_model(self, model_name: str) -> bool:
        """Update the current model"""
        # Check if model exists
        models = self.list_models()
        available_models = [model["name"] for model in models.get("models", [])]
        
        if model_name not in available_models:
            self.logger.warning(f"Model {model_name} not found in available models")
            return False
        
        self.model = model_name
        self.logger.info(f"Updated model to {model_name}")
        return True
    
    def update_parameters(self, **params) -> None:
        """Update generation parameters"""
        self.default_params.update(params)
        self.logger.info(f"Updated parameters: {params}")
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a model"""
        target_model = model_name or self.model
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": target_model},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to get model info for {target_model}: {e}")
            return {}


# Factory function for creating appropriate LLM client
def create_llm_client(config_manager=None, legacy_mode=False) -> Any:
    """Create an LLM client instance"""
    if legacy_mode or config_manager is None:
        # Return legacy Ollama-only client
        return LLMClient()
    else:
        # Return enhanced multi-provider client
        return LLMClientFactory.create_from_config(config_manager)
