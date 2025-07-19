"""
OpenAI/ChatGPT LLM Provider implementation
"""

import requests
import time
import json
from typing import Dict, Any, List
from .base_provider import BaseLLMProvider, LLMResponse, LLMConfig


class OpenAIProvider(BaseLLMProvider):
    """OpenAI/ChatGPT LLM provider"""
    
    SUPPORTED_MODELS = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k"
    ]
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.openai.com/v1"
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"OpenAI health check failed: {e}")
            return False
    
    def list_models(self) -> Dict[str, Any]:
        """List available OpenAI models"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            # Filter to only supported models
            supported_models = [
                model for model in data.get("data", [])
                if model.get("id") in self.SUPPORTED_MODELS
            ]
            
            return {"models": supported_models}
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to list OpenAI models: {e}")
            return {"models": []}
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using OpenAI API"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Merge config params with provided kwargs
            temperature = kwargs.get("temperature", self.config.temperature)
            max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
            
            # Build messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert SQL analyst and database query assistant. Provide clear, accurate, and efficient SQL queries."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            payload = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": kwargs.get("top_p", 1.0),
                "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
                "presence_penalty": kwargs.get("presence_penalty", 0.0)
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            response_time = time.time() - start_time
            
            # Extract content from response
            content = ""
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
            
            # Extract token usage
            tokens_used = 0
            if "usage" in data:
                tokens_used = data["usage"].get("total_tokens", 0)
            
            return LLMResponse(
                content=content,
                success=True,
                model=data.get("model"),
                tokens_used=tokens_used,
                response_time=response_time,
                provider="openai"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate text with OpenAI: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=str(e),
                provider="openai"
            )
    
    def estimate_cost(self, tokens_used: int, model: str = None) -> float:
        """Estimate cost based on token usage"""
        model = model or self.config.model
        
        # Token pricing per 1K tokens (as of 2024)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004}
        }
        
        if model not in pricing:
            return 0.0
        
        # Rough estimation (assuming 70% input, 30% output)
        input_tokens = int(tokens_used * 0.7)
        output_tokens = int(tokens_used * 0.3)
        
        cost = (input_tokens / 1000 * pricing[model]["input"] + 
                output_tokens / 1000 * pricing[model]["output"])
        
        return round(cost, 6)
