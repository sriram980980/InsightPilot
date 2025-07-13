"""
Prompt builder for structured LLM prompts
"""

import logging
from typing import List, Dict, Any
from adapters.base_adapter import TableSchema


class PromptBuilder:
    """Builder for structured LLM prompts"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def build_sql_prompt(self, schema_info: str, question: str) -> str:
        """Build SQL generation prompt"""
        prompt = f"""You are an expert SQL query generator. Given the database schema and a natural language question, generate a valid SQL SELECT query.

### DATABASE SCHEMA ###
{schema_info}

### RULES ###
1. Only generate SELECT queries
2. Do not use any DDL or DML operations (CREATE, DROP, INSERT, UPDATE, DELETE)
3. Use proper SQL syntax and formatting
4. Include appropriate WHERE clauses for filtering
5. Use JOINs when needed to relate tables
6. Add LIMIT clauses to prevent large result sets (max 1000 rows)
7. Use proper aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
8. Always use table aliases for better readability

### QUESTION ###
{question}

### SQL QUERY ###
"""
        return prompt
    
    def build_mongodb_prompt(self, schema_info: str, question: str) -> str:
        """Build MongoDB aggregation prompt"""
        prompt = f"""You are an expert MongoDB query generator. Given the collection schema and a natural language question, generate a valid MongoDB aggregation pipeline.

### COLLECTION SCHEMA ###
{schema_info}

### RULES ###
1. Only generate aggregation pipelines using find() or aggregate()
2. Use proper MongoDB operators ($match, $group, $sort, $limit, etc.)
3. Include appropriate $match stages for filtering
4. Use $limit stage to prevent large result sets (max 1000 documents)
5. Use proper aggregation operators ($sum, $avg, $count, etc.) when appropriate
6. Format the output as a valid MongoDB query

### QUESTION ###
{question}

### MONGODB QUERY ###
"""
        return prompt
    
    def build_explain_prompt(self, query: str) -> str:
        """Build prompt for explaining SQL queries"""
        prompt = f"""You are an expert SQL query explainer. Given a SQL query, provide a detailed explanation of its purpose and logic.
### SQL QUERY ###
{query}

### EXPLANATION ###
"""
        return prompt   