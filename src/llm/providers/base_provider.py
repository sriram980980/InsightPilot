"""
Base LLM Provider interface for supporting multiple LLM services
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging


@dataclass
class LLMResponse:
    """Standardized LLM response structure"""
    content: str
    success: bool
    error: Optional[str] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    provider: Optional[str] = None


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 1000
    timeout: int = 180
    additional_params: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the LLM service is available"""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using the LLM"""
        pass
    
    @abstractmethod
    def list_models(self) -> Dict[str, Any]:
        """List available models for this provider"""
        pass
    
    def generate_sql(self, schema_info: str, question: str) -> LLMResponse:
        """Generate SQL query from schema and question using LLM"""
        try:
            from llm.prompt_builder import PromptBuilder
        except ImportError:
            # Handle direct execution case
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from llm.prompt_builder import PromptBuilder
        
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_sql_prompt(schema_info, question)
        return self.generate(prompt)

    def generate_sql_custom_prompt(self, custom_prompt: str) -> LLMResponse:
        """Generate SQL query using a custom prompt (for retry scenarios)"""
        return self.generate(custom_prompt)

    def generate_mongodb_query(self, schema_info: str, question: str) -> LLMResponse:
        """Generate MongoDB aggregation query from schema and question using LLM"""
        try:
            from llm.prompt_builder import PromptBuilder
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from llm.prompt_builder import PromptBuilder
        
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_mongodb_prompt(schema_info, question)
        return self.generate(prompt)

    def recommend_chart(self, columns: List[str], sample_data: List[List[Any]], question: str, user_hint: str = "") -> LLMResponse:
        """Ask LLM to recommend the best chart type for the data"""
        try:
            from llm.prompt_builder import PromptBuilder
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from llm.prompt_builder import PromptBuilder
        
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_chart_recommendation_prompt(columns, sample_data, question, user_hint)
        return self.generate(prompt)

    def explain_query(self, query: str) -> LLMResponse:
        """Ask LLM to explain the generated query"""
        try:
            from llm.prompt_builder import PromptBuilder
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from llm.prompt_builder import PromptBuilder
        
        prompt_builder = PromptBuilder()
        prompt = prompt_builder.build_explain_prompt(query)
        return self.generate(prompt)
    
    def update_model(self, model_name: str) -> bool:
        """Update the current model"""
        self.config.model = model_name
        return True
    
    def update_parameters(self, **params) -> None:
        """Update generation parameters"""
        for key, value in params.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            elif self.config.additional_params is None:
                self.config.additional_params = {key: value}
            else:
                self.config.additional_params[key] = value
