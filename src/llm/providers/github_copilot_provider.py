"""
GitHub Copilot LLM Provider implementation
"""

import requests
import time
import json
from typing import Dict, Any
from .base_provider import BaseLLMProvider, LLMResponse, LLMConfig


class GitHubCopilotProvider(BaseLLMProvider):
    """GitHub Copilot LLM provider via GitHub API"""
    
    SUPPORTED_MODELS = [
        "gpt-4o",
        "gpt-4o-mini", 
        "claude-3.5-sonnet",
        "o1-preview",
        "o1-mini"
    ]
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_key  # GitHub Personal Access Token
        self.base_url = config.base_url or "https://models.inference.ai.azure.com"
        
        if not self.api_key:
            raise ValueError("GitHub Personal Access Token is required for Copilot access")
    
    def health_check(self) -> bool:
        """Check if GitHub Copilot API is accessible"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple request
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"GitHub Copilot health check failed: {e}")
            return False
    
    def list_models(self) -> Dict[str, Any]:
        """List available GitHub Copilot models"""
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
            
            if response.status_code == 200:
                data = response.json()
                return {"models": data.get("data", [])}
            else:
                # Return supported models as fallback
                return {
                    "models": [
                        {"id": model, "object": "model"} 
                        for model in self.SUPPORTED_MODELS
                    ]
                }
                
        except requests.RequestException as e:
            self.logger.error(f"Failed to list GitHub Copilot models: {e}")
            return {
                "models": [
                    {"id": model, "object": "model"} 
                    for model in self.SUPPORTED_MODELS
                ]
            }
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using GitHub Copilot API"""
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
                    "content": "You are GitHub Copilot, an AI coding assistant. You excel at SQL queries, database analysis, and data insights. Provide accurate, efficient, and well-commented code."
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
                "top_p": kwargs.get("top_p", 0.95),
                "stream": False
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
                provider="github_copilot"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate text with GitHub Copilot: {e}")
            return LLMResponse(
                content="",
                success=False,
                error=str(e),
                provider="github_copilot"
            )
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make a lightweight request to check rate limits
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=5
            )
            
            rate_limit_info = {
                "requests_remaining": response.headers.get("x-ratelimit-remaining"),
                "requests_limit": response.headers.get("x-ratelimit-limit"),
                "reset_time": response.headers.get("x-ratelimit-reset"),
                "retry_after": response.headers.get("retry-after")
            }
            
            return rate_limit_info
            
        except Exception as e:
            self.logger.error(f"Failed to get rate limits: {e}")
            return {}
    
    def validate_token(self) -> bool:
        """Validate GitHub Personal Access Token"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/vnd.github+json"
            }
            
            response = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Token validation failed: {e}")
            return False
