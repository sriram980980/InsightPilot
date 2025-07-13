"""
LLM client for Ollama integration
"""

import json
import logging
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM response structure"""
    content: str
    success: bool
    error: Optional[str] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None


class LLMClient:
    """Client for communicating with Ollama LLM server"""
    
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
    
    def health_check(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
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
