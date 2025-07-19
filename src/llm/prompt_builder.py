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
3. Use proper SQL syntax and formatting compatible with MySQL
4. Include appropriate WHERE clauses for filtering
5. Use JOINs when needed to relate tables
6. Add LIMIT clauses to prevent large result sets (max 1000 rows)
7. Use proper aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
8. Always use table aliases for better readability
9. When calculating percentages, use subqueries in the SELECT clause, not in nested FROM clauses
10. Avoid complex nested subqueries that reference group functions from outer queries
11. Use HAVING clause instead of WHERE for filtering on aggregate functions
12. For percentage calculations, calculate totals in separate subqueries

### MYSQL SPECIFIC GUIDELINES ###
- Use backticks around table/column names if they contain special characters
- For percentage calculations, structure queries like: (value / (SELECT SUM(column) FROM table)) * 100
- Avoid referencing aggregate function results by alias in the same query level
- Use proper GROUP BY clauses for all non-aggregate columns in SELECT

### QUESTION ###
{question}

### SQL QUERY ###
Generate only the SQL query without any additional text or formatting:"""
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
    
    def format_schema_info(self, schemas: List[TableSchema]) -> str:
        """Format schema information for prompts"""
        schema_text = ""
        
        for schema in schemas:
            schema_text += f"\n### TABLE: {schema.name} ###\n"
            schema_text += "Columns:\n"
            
            for column in schema.columns:
                schema_text += f"  - {column['name']} ({column['type']})"
                if column['name'] in schema.primary_keys:
                    schema_text += " [PRIMARY KEY]"
                if not column.get('nullable', True):
                    schema_text += " [NOT NULL]"
                schema_text += "\n"
            
            if schema.foreign_keys:
                schema_text += "Foreign Keys:\n"
                for fk in schema.foreign_keys:
                    schema_text += f"  - {fk['column']} -> {fk['references']}\n"
            
            schema_text += "\n"
        
        return schema_text
    
    def build_chart_suggestion_prompt(self, query_result: str, question: str) -> str:
        """Build prompt for chart type suggestions"""
        prompt = f"""You are an expert data visualization consultant. Given the query result data and the original question, suggest the most appropriate chart type and configuration.

### ORIGINAL QUESTION ###
{question}

### QUERY RESULT STRUCTURE ###
{query_result}

### CHART SUGGESTION RULES ###
1. Consider the data types (categorical, numerical, temporal)
2. Consider the number of dimensions
3. Consider the story the data should tell
4. Suggest appropriate chart types: bar, line, pie, scatter, histogram, etc.
5. Provide specific configuration recommendations

### CHART RECOMMENDATION ###
Chart Type: 
Reasoning: 
Configuration:
"""
        return prompt
    
    def build_error_explanation_prompt(self, query: str, error: str) -> str:
        """Build prompt for explaining query errors"""
        prompt = f"""You are an expert database troubleshooter. Given a query and its error message, provide a clear explanation of what went wrong and how to fix it.

### QUERY ###
{query}

### ERROR MESSAGE ###
{error}

### ERROR ANALYSIS ###
Problem: 
Cause: 
Solution: 
"""
        return prompt
    
    def build_optimization_prompt(self, query: str, execution_plan: str = "") -> str:
        """Build prompt for query optimization suggestions"""
        prompt = f"""You are an expert SQL performance optimizer. Given a query and optionally its execution plan, provide optimization suggestions.

### QUERY ###
{query}

### EXECUTION PLAN ###
{execution_plan if execution_plan else 'No execution plan provided'}

### OPTIMIZATION SUGGESTIONS ###
1. Performance Analysis:
2. Bottlenecks Identified:
3. Optimization Recommendations:
4. Optimized Query (if applicable):
"""
        return prompt
    
    def build_chart_recommendation_prompt(self, columns: List[str], sample_data: List[List[Any]], question: str, user_hint: str = "") -> str:
        """Build prompt for chart type recommendation"""
        # Format sample data for the prompt
        data_preview = ""
        if sample_data:
            data_preview = "Sample Data (first 5 rows):\n"
            for i, row in enumerate(sample_data[:5]):
                data_preview += f"Row {i+1}: {dict(zip(columns, row))}\n"
        
        user_hint_text = f"\n### USER PREFERENCE ###\n{user_hint}\n" if user_hint.strip() else ""
        
        prompt = f"""You are an expert data visualization consultant. Given the query result data and the original question, recommend the most appropriate chart type and provide configuration details.

### QUERY CONTEXT ###
Original Question: {question}

### DATA STRUCTURE ###
Columns: {columns}
Number of columns: {len(columns)}
{data_preview}
{user_hint_text}
### AVAILABLE CHART TYPES ###
- bar: For categorical comparisons
- line: For trends over time or continuous data
- pie: For part-to-whole relationships (max 8 categories)
- scatter: For correlation between two numeric variables
- histogram: For distribution of single numeric variable
- table: For detailed data viewing

### INSTRUCTIONS ###
Respond ONLY with a JSON object containing:
{{
    "chart_type": "recommended_type",
    "reasoning": "why this chart type is best",
    "x_column": "column_name_for_x_axis",
    "y_column": "column_name_for_y_axis", 
    "title": "suggested_chart_title",
    "considerations": ["any_important_notes"]
}}

### CHART RECOMMENDATION ###
"""
        return prompt