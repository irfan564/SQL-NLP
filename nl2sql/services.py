import os
import re
import time
import requests
from django.db import connection, transaction

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
6. Salary statistics must exclude undisclosed salaries, i.e. WHERE salary_midpoint_lpa > 0 (also exclude NULL). Always mention this in a SQL comment.
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


DANGEROUS_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE",
    "GRANT", "REVOKE", "COPY", "CALL", "DO", "EXECUTE",
    "PG_SLEEP", "PG_READ_FILE", "PG_LS_DIR", "LO_IMPORT", "LO_EXPORT",
    "DBLINK", "SET_CONFIG", "INFORMATION_SCHEMA", "PG_CATALOG"
]


def strip_sql_comments(sql: str) -> str:
    """
    Strips single-line (-- ...) and multi-line (/* ... */) SQL comments
    while safely preserving string literals.
    """
    pattern = r"('(?:''|[^'])*')|(--[^\r\n]*)|(/\*[\s\S]*?\*/)"

    def replace_match(m):
        if m.group(1):
            return m.group(1)
        return " "

    return re.sub(pattern, replace_match, sql)


def mask_string_literals(sql: str) -> str:
    """
    Replaces string literals with a placeholder so keyword and symbol checks
    do not inspect characters inside quotes.
    """
    return re.sub(r"'(?:''|[^'])*'", "'__STR__'", sql)


def validate_sql(sql: str) -> str:
    """
    Strict SQL validation and safety enforcement:
    a) Strips SQL comments (-- and /* */) before checking;
    b) Allows exactly ONE statement (rejects any semicolon followed by more text);
    c) Requires the statement to start with SELECT or WITH;
    d) Rejects dangerous keywords and functions as whole words:
       INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE,
       COPY, CALL, DO, EXECUTE, pg_sleep, pg_read_file, pg_ls_dir, lo_import,
       lo_export, dblink, set_config, information_schema, pg_catalog;
    e) Only allows the table indian_tech_jobs (and query-defined CTEs);
    f) Appends LIMIT 500 if no LIMIT is present.

    Returns the validated SQL query string.
    Raises ValueError with a clear, safe message if validation fails.
    """
    if not sql or not isinstance(sql, str):
        raise ValueError("SQL query must be a non-empty string.")

    # a) Strip SQL comments
    clean_sql = strip_sql_comments(sql).strip()
    if not clean_sql:
        raise ValueError("SQL query is empty or contains only comments.")

    masked = mask_string_literals(clean_sql)

    # b) Exactly one statement: reject any semicolon followed by non-whitespace/non-semicolon text
    if re.search(r";\s*[^;\s]", masked):
        raise ValueError("Multiple SQL statements are not permitted. Only a single query is allowed.")

    # Strip any trailing semicolons
    clean_sql = clean_sql.rstrip().rstrip(";").strip()
    masked = mask_string_literals(clean_sql)

    # c) Statement must start with SELECT or WITH
    if not re.match(r"^\s*(SELECT|WITH)\b", clean_sql, re.IGNORECASE):
        raise ValueError("Query must start with SELECT or WITH.")

    # d) Reject dangerous keywords and functions as whole words
    kw_pattern = r"\b(" + "|".join(re.escape(k) for k in DANGEROUS_KEYWORDS) + r")\b"
    kw_match = re.search(kw_pattern, masked, re.IGNORECASE)
    if kw_match:
        raise ValueError(f"Disallowed keyword or function detected: '{kw_match.group(0)}'.")

    # e) Only allow the table indian_tech_jobs (and CTEs defined within WITH)
    cte_names = set()
    if re.match(r"^\s*WITH\b", masked, re.IGNORECASE):
        cte_matches = re.findall(
            r"(?:WITH|,)\s*([a-zA-Z0-9_]+)\s*(?:\([^)]*\))?\s*AS\s*\(",
            masked,
            re.IGNORECASE
        )
        for c in cte_matches:
            cte_names.add(c.lower())

    allowed_tables = {"indian_tech_jobs"} | cte_names

    # Ensure indian_tech_jobs is referenced
    if not re.search(r"\bindian_tech_jobs\b", masked, re.IGNORECASE):
        raise ValueError("Query must reference the 'indian_tech_jobs' table.")

    # Check FROM clauses
    from_matches = re.finditer(
        r"\bFROM\s+([a-zA-Z0-9_.\"',\s]+?)(?=\bWHERE\b|\bGROUP\b|\bORDER\b|\bLIMIT\b|\bHAVING\b|\bWINDOW\b|\bJOIN\b|\bINNER\b|\bLEFT\b|\bRIGHT\b|\bFULL\b|\bCROSS\b|\bON\b|\bUNION\b|\)|;|$)",
        masked,
        re.IGNORECASE
    )
    for fm in from_matches:
        clause = fm.group(1).strip()
        if clause.startswith("("):
            continue
        for part in clause.split(","):
            part = part.strip()
            if not part or part.startswith("("):
                continue
            table_token = part.split()[0].strip().strip('",;').lower()
            if table_token.startswith("public."):
                table_token = table_token[7:]
            if table_token and table_token not in allowed_tables:
                raise ValueError(f"Access to table '{table_token}' is not permitted. Only 'indian_tech_jobs' is allowed.")

    # Check JOIN clauses
    join_matches = re.finditer(
        r"\b(?:JOIN|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|CROSS\s+JOIN)\s+([a-zA-Z0-9_.\"]+)",
        masked,
        re.IGNORECASE
    )
    for jm in join_matches:
        clause = jm.group(1).strip()
        if clause.startswith("("):
            continue
        table_token = clause.split()[0].strip().strip('",;').lower()
        if table_token.startswith("public."):
            table_token = table_token[7:]
        if table_token and table_token not in allowed_tables:
            raise ValueError(f"Access to table '{table_token}' is not permitted. Only 'indian_tech_jobs' is allowed.")

    # f) Append LIMIT 500 if no LIMIT is present
    if not re.search(r"\bLIMIT\s+\d+\b", masked, re.IGNORECASE):
        clean_sql = clean_sql + " LIMIT 500"

    return clean_sql


def execute_sql_query(sql_query: str) -> dict:
    """
    Executes a validated read-only SQL query against the database inside
    a read-only transaction with a 5-second statement timeout.
    Returns results metadata dict with columns, rows, execution time, and chart data hints.
    """
    validated_sql = validate_sql(sql_query)
    start_time = time.time()

    with transaction.atomic():
        with connection.cursor() as cursor:
            if connection.vendor == "postgresql":
                cursor.execute("SET LOCAL TRANSACTION READ ONLY;")
                cursor.execute("SET LOCAL statement_timeout = '5s';")

            cursor.execute(validated_sql)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            raw_rows = cursor.fetchall()
            rows = [list(row) for row in raw_rows]

    execution_time_ms = round((time.time() - start_time) * 1000, 2)

    # Detect Chart Data suitability (for aggregate queries with category column + numeric column)
    chart_data = None
    if len(columns) >= 2 and 0 < len(rows) <= 30:
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
        "chart_data": chart_data,
        "executed_sql": validated_sql
    }

