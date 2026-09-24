import os
import re
import time
import requests
from django.db import connection

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Primary & fallback models on OpenRouter
MODELS = [
    "meta-llama/llama-3.3-70b-instruct",
    "anthropic/claude-3.5-sonnet",
    "deepseek/deepseek-r1",
    "openai/gpt-4o-mini"
]

SCHEMA_CONTEXT = """
Database Engine: PostgreSQL (Supabase)
Table Name: indian_tech_jobs

Columns and Data Types:
- job_id (INTEGER PRIMARY KEY) - Unique job identifier
- job_title (TEXT) - Name of the position e.g., 'Data Scientist', 'AI/ML Engineer', 'Full Stack Developer'
- company_name (TEXT) - Company offering the role e.g. 'Cisco', 'Google', 'Wipro', 'Genpact'
- company_rating (DOUBLE PRECISION) - Rating out of 5.0 e.g. 4.1, 4.4
- location (TEXT) - Detailed job location string e.g. 'Bengaluru', 'Hybrid - Gurugram, Bengaluru'
- primary_city (TEXT) - Cleaned main city name e.g. 'Bangalore', 'Hyderabad', 'Pune', 'Mumbai', 'Delhi', 'Noida', 'Gurgaon'
- role_category (TEXT) - Role category classification e.g. 'Data Scientist', 'Software Developer'
- experience_raw (TEXT) - Experience text e.g. '5-10 Yrs', '0-3 Yrs'
- experience_min_yrs (DOUBLE PRECISION) - Minimum required experience in years e.g. 0.0, 3.0, 5.0
- experience_max_yrs (DOUBLE PRECISION) - Maximum required experience in years e.g. 3.0, 10.0
- salary_raw (TEXT) - Raw salary text e.g. '15-25 Lacs PA', 'Not Disclosed'
- salary_min_lpa (DOUBLE PRECISION) - Minimum salary in Lakhs Per Annum (LPA)
- salary_max_lpa (DOUBLE PRECISION) - Maximum salary in Lakhs Per Annum (LPA)
- salary_disclosed (BOOLEAN) - True if salary range is disclosed, False otherwise
- salary_midpoint_lpa (DOUBLE PRECISION) - Midpoint salary in Lakhs Per Annum (LPA)
- skills_required (TEXT) - Required skills string e.g. 'Python, SQL, Machine Learning, Analytics'
- skills_count (INTEGER) - Total number of skills required
- job_description (TEXT) - Snippet of job description
- work_mode (TEXT) - Work setup e.g. 'On-site', 'Hybrid', 'Remote'
- company_size_bucket (TEXT) - Size category e.g. 'Large (1000+)', 'Small/Startup (<100)'
- skill_domain (TEXT) - Tech domain e.g. 'AI/ML/DL', 'Data Science', 'Business Intelligence'
- salary_tier (TEXT) - Salary classification e.g. 'Senior (10-20 LPA)', 'Undisclosed'
- experience_tier (TEXT) - Tier classification e.g. 'Fresher', 'Mid (3-5 Yrs)', 'Senior (6-8 Yrs)'
- is_senior (BOOLEAN) - True if senior role
- is_fresher_friendly (BOOLEAN) - True if 0-2 yrs experience or marked fresher
- salary_negotiable (BOOLEAN) - True if negotiable

SQL Rules:
1. Always generate valid PostgreSQL SELECT statements ONLY.
2. NEVER use write statements (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE).
3. Use case-insensitive searching with ILIKE for text matching (e.g. skills_required ILIKE '%python%').
4. Always add 'LIMIT 100' unless the query uses explicit aggregations (GROUP BY, COUNT, AVG, MAX, MIN).
5. If asking for averages or counts, use round(AVG(...)::numeric, 2) or COUNT(*).
"""

def generate_sql_from_openrouter(prompt: str) -> tuple[str, str]:
    """
    Sends natural language prompt to OpenRouter API and extracts clean SQL statement.
    Returns (sql_query, model_used).
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is missing from environment variables.")

    system_instruction = (
        "You are an expert SQL Translator for PostgreSQL databases. "
        "Convert user natural language prompts into precise, valid SQL queries using the schema provided.\n\n"
        f"{SCHEMA_CONTEXT}\n\n"
        "OUTPUT FORMAT REQUIREMENT:\n"
        "Return ONLY the SQL query code block marked with ```sql ... ```. "
        "Do NOT include conversational introduction or commentary outside the query code block."
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ]

    last_error = None
    for model in MODELS:
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Django-SQL-NLP-App"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 600
            }

            resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                
                # Extract SQL snippet from code block if present
                sql_match = re.search(r"```sql\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
                if sql_match:
                    sql_query = sql_match.group(1).strip()
                else:
                    # Fallback code block match
                    code_match = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL)
                    sql_query = code_match.group(1).strip() if code_match else content.strip()
                
                # Strip trailing semicolon if needed or ensure safe query text
                sql_query = sql_query.rstrip(";")
                return sql_query, model
            else:
                last_error = f"Model {model} returned status {resp.status_code}: {resp.text}"
        except Exception as e:
            last_error = f"Error calling OpenRouter ({model}): {str(e)}"

    raise RuntimeError(f"Failed to generate SQL from OpenRouter: {last_error}")


def execute_sql_query(sql_query: str) -> dict:
    """
    Executes a read-only SQL query against Supabase PostgreSQL database via Django connection.
    Returns results metadata dict with columns, rows, execution time, and chart data hints.
    """
    # Security Validation: Ensure query is read-only SELECT statement
    clean_sql = sql_query.strip().upper()
    forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
    for kw in forbidden:
        if re.search(rf"\b{kw}\b", clean_sql):
            raise ValueError(f"Security Alert: Only SELECT queries are permitted. Query contains disallowed keyword: '{kw}'.")

    start_time = time.time()
    
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description] if cursor.description else []
        raw_rows = cursor.fetchall()
        
        # Convert row tuples to list of lists (JSON serializable)
        rows = [list(row) for row in raw_rows]
        
    execution_time_ms = round((time.time() - start_time) * 1000, 2)

    # Detect Chart Data suitability (for aggregate queries with category column + numeric column)
    chart_data = None
    if len(columns) >= 2 and len(rows) > 0 and len(rows) <= 30:
        # Check if 1st column is label/string and 2nd column is numeric
        labels = [str(r[0]) if r[0] is not None else "N/A" for r in rows]
        try:
            values = [float(r[1]) if r[1] is not None else 0.0 for r in rows]
            chart_data = {
                "label_column": columns[0],
                "value_column": columns[1],
                "labels": labels,
                "values": values
            }
        except (ValueError, TypeError):
            chart_data = None

    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "execution_time_ms": execution_time_ms,
        "chart_data": chart_data
    }
