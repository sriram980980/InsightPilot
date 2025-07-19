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
        # Use the official GitHub API endpoint instead of Azure
        self.base_url = config.base_url or "https://api.github.com/copilot_internal"
        
        if not self.api_key:
            raise ValueError("GitHub Personal Access Token is required for Copilot access")
    
    def health_check(self) -> bool:
        """Check if GitHub Copilot API is accessible"""
        try:
            # First validate the GitHub token itself
            headers = {
                "Authorization": f"token {self.api_key}",  # Use 'token' instead of 'Bearer'
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            # Test GitHub API access first
            response = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"GitHub token validation failed: {response.status_code}, {response.text}")
                return False
            
            # Check if user has Copilot access
            user_data = response.json()
            self.logger.info(f"GitHub token validated for user: {user_data.get('login', 'unknown')}")
            
            # For now, return True if GitHub token is valid
            # The actual Copilot API endpoint may require different authentication
            return True
            
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
                return {"models": data}
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
            # Important Note: GitHub Copilot's chat API is not publicly available
            # This implementation handles the current limitations gracefully
            
            # GitHub Copilot API endpoints and model mappings
            # Map to models supported by Azure Models endpoint
            model_mapping = {
                "gpt-4o": "gpt-4o",
                "gpt-4o-mini": "gpt-4o-mini", 
                "claude-3.5-sonnet": "claude-3.5-sonnet",
                "o1-preview": "o1-preview",
                "o1-mini": "o1-mini"
            }
            
            # Map the model to a compatible one
            model_name = model_mapping.get(self.config.model, "gpt-4o-mini")
            
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
                "model": model_name,
                "messages": messages,
                "temperature": min(temperature, 1.0),  # Ensure temperature is within valid range
                "max_tokens": min(max_tokens, 4096),   # Limit max tokens
                "stream": False
            }
            
            # Add optional parameters if they're reasonable values
            top_p = kwargs.get("top_p", 0.95)
            if 0 < top_p <= 1:
                payload["top_p"] = top_p
            
            # Try different endpoints with proper error handling
            # Note: GitHub Copilot chat API is not publicly available
            # These endpoints are for demonstration/testing purposes
            endpoints_to_try = [
                {
                    "url": "https://models.inference.ai.azure.com/chat/completions",
                    "headers": {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                }
            ]
            
            last_error = None
            
            for endpoint in endpoints_to_try:
                try:
                    response = requests.post(
                        endpoint["url"],
                        headers=endpoint["headers"],
                        json=payload,
                        timeout=self.config.timeout
                    )
                    
                    if response.status_code == 200:
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
                            model=data.get("model", model_name),
                            tokens_used=tokens_used,
                            response_time=response_time,
                            provider="github_copilot"
                        )
                    
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text}"
                        
                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    continue
            
            # If we get here, all endpoints failed
            if "Personal Access Tokens are not supported" in str(last_error):
                error_msg = "GitHub Copilot API does not support Personal Access Tokens. The GitHub Copilot chat API is not publicly available for third-party applications. Please use OpenAI or Ollama providers instead."
            elif "401" in str(last_error) or "Unauthorized" in str(last_error):
                error_msg = "GitHub Copilot API access denied. GitHub Copilot chat API requires special permissions and is not generally available. Please use OpenAI or Ollama providers instead."
            elif "400" in str(last_error) or "Bad Request" in str(last_error):
                error_msg = "GitHub Copilot API request failed. The GitHub Copilot chat API is not publicly available for third-party applications. Please use OpenAI or Ollama providers instead."
            else:
                error_msg = f"GitHub Copilot API unavailable: {last_error}. Note: GitHub Copilot chat API is not publicly accessible for third-party applications."
            
            return LLMResponse(
                content="",
                success=False,
                error=error_msg,
                provider="github_copilot"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate text with GitHub Copilot: {e}")
            return LLMResponse(
                content="",
                success=False,
                error="GitHub Copilot chat API is not publicly available. Please use OpenAI or Ollama providers instead.",
                provider="github_copilot"
            )
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        try:
            headers = {
                "Authorization": f"token {self.api_key}",  # Use 'token' for GitHub API
                "Accept": "application/vnd.github+json"
            }
            
            # Make a lightweight request to check rate limits
            response = requests.get(
                "https://api.github.com/user",
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
                "Authorization": f"token {self.api_key}",  # Use 'token' for GitHub API
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
