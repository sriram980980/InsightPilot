"""
Ollama LLM Provider implementation
"""

import requests
import time
from typing import Dict, Any
from .base_provider import BaseLLMProvider, LLMResponse, LLMConfig


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider for local models"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or f"http://localhost:11434"
        
    def health_check(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Ollama health check failed: {e}")
            return False
    
    def list_models(self) -> Dict[str, Any]:
        """List available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to list Ollama models: {e}")
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
        """Generate text using Ollama"""
        start_time = time.time()
        
        try:
            # Merge config params with provided kwargs
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            top_p = kwargs.get("top_p", 0.9)
            
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=data.get("response", ""),
                success=True,
                model=data.get("model"),
                tokens_used=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                response_time=response_time,
                provider="ollama"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate text with Ollama: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=str(e),
                provider="ollama"
            )
    
    def get_model_info(self, model_name: str = None) -> Dict[str, Any]:
        """Get information about an Ollama model"""
        target_model = model_name or self.config.model
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
