"""
Tests for LLM client functionality
"""

import pytest
import unittest.mock as mock
from llm.llm_client import LLMClient, LLMResponse
from llm.prompt_builder import PromptBuilder
from adapters.base_adapter import TableSchema


class TestLLMClient:
    """Test LLM client functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = LLMClient(host="localhost", port=11434, model="mistral:7b")
    
    @mock.patch('llm.llm_client.requests.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check"""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.client.health_check()
        
        assert result is True
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5)
    
    @mock.patch('llm.llm_client.requests.get')
    def test_health_check_failure(self, mock_get):
        """Test health check failure"""
        mock_get.side_effect = Exception("Connection failed")
        
        result = self.client.health_check()
        
        assert result is False
    
    @mock.patch('llm.llm_client.requests.post')
    def test_generate_success(self, mock_post):
        """Test successful LLM generation"""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "SELECT * FROM users WHERE id = 1",
            "model": "mistral:7b"
        }
        mock_post.return_value = mock_response
        
        result = self.client.generate("Generate a SQL query")
        
        assert result.success is True
        assert result.content == "SELECT * FROM users WHERE id = 1"
        assert result.model == "mistral:7b"
        mock_post.assert_called_once()
    
    @mock.patch('llm.llm_client.requests.post')
    def test_generate_failure(self, mock_post):
        """Test LLM generation failure"""
        mock_post.side_effect = Exception("Request failed")
        
        result = self.client.generate("Generate a SQL query")
        
        assert result.success is False
        assert result.error is not None
        assert result.content == ""
    
    def test_update_model(self):
        """Test model update"""
        new_model = "llama3:8b"
        
        with mock.patch.object(self.client, 'list_models') as mock_list:
            mock_list.return_value = {"models": [{"name": "llama3:8b"}]}
            
            result = self.client.update_model(new_model)
            
            assert result is True
            assert self.client.model == new_model
    
    def test_update_parameters(self):
        """Test parameter update"""
        new_params = {"temperature": 0.5, "max_tokens": 500}
        
        self.client.update_parameters(**new_params)
        
        assert self.client.default_params["temperature"] == 0.5
        assert self.client.default_params["max_tokens"] == 500


class TestPromptBuilder:
    """Test prompt builder functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.builder = PromptBuilder()
        self.sample_schema = [
            TableSchema(
                name="users",
                columns=[
                    {"name": "id", "type": "int", "nullable": False},
                    {"name": "name", "type": "varchar", "nullable": False},
                    {"name": "email", "type": "varchar", "nullable": True}
                ],
                primary_keys=["id"],
                foreign_keys=[]
            ),
            TableSchema(
                name="orders",
                columns=[
                    {"name": "id", "type": "int", "nullable": False},
                    {"name": "user_id", "type": "int", "nullable": False},
                    {"name": "total", "type": "decimal", "nullable": False}
                ],
                primary_keys=["id"],
                foreign_keys=[{"column": "user_id", "references": "users.id"}]
            )
        ]
    
    def test_build_sql_prompt(self):
        """Test SQL prompt building"""
        schema_info = self.builder.format_schema_info(self.sample_schema)
        question = "Show all users with their order totals"
        
        prompt = self.builder.build_sql_prompt(schema_info, question)
        
        assert "DATABASE SCHEMA" in prompt
        assert "users" in prompt
        assert "orders" in prompt
        assert question in prompt
        assert "SELECT" in prompt
        assert "RULES" in prompt
    
    def test_build_mongodb_prompt(self):
        """Test MongoDB prompt building"""
        schema_info = self.builder.format_schema_info(self.sample_schema)
        question = "Show all users with their order count"
        
        prompt = self.builder.build_mongodb_prompt(schema_info, question)
        
        assert "COLLECTION SCHEMA" in prompt
        assert "aggregation" in prompt
        assert question in prompt
        assert "MONGODB QUERY" in prompt
    
    def test_build_explain_prompt(self):
        """Test explain prompt building"""
        query = "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id"
        
        prompt = self.builder.build_explain_prompt(query)
        
        assert "QUERY" in prompt
        assert query in prompt
        assert "EXPLANATION" in prompt
    
    def test_format_schema_info(self):
        """Test schema information formatting"""
        schema_text = self.builder.format_schema_info(self.sample_schema)
        
        assert "Table: users" in schema_text
        assert "Table: orders" in schema_text
        assert "Primary Key(s): id" in schema_text
        assert "Foreign Key(s): user_id -> users.id" in schema_text
        assert "id (int) NOT NULL" in schema_text
        assert "name (varchar) NOT NULL" in schema_text
        assert "email (varchar) NULL" in schema_text
    
    def test_build_chart_suggestion_prompt(self):
        """Test chart suggestion prompt building"""
        query_result = "columns: [name, order_count], rows: [[John, 5], [Jane, 3]]"
        question = "Show users with their order counts"
        
        prompt = self.builder.build_chart_suggestion_prompt(query_result, question)
        
        assert "ORIGINAL QUESTION" in prompt
        assert "QUERY RESULT STRUCTURE" in prompt
        assert "CHART RECOMMENDATION" in prompt
        assert question in prompt
        assert query_result in prompt
    
    def test_build_error_explanation_prompt(self):
        """Test error explanation prompt building"""
        query = "SELECT * FROM nonexistent_table"
        error = "Table 'nonexistent_table' doesn't exist"
        
        prompt = self.builder.build_error_explanation_prompt(query, error)
        
        assert "QUERY" in prompt
        assert "ERROR" in prompt
        assert "ANALYSIS" in prompt
        assert query in prompt
        assert error in prompt


if __name__ == "__main__":
    pytest.main([__file__])
