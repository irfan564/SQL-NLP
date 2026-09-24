import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sql_nlp_project.settings')
django.setup()

from nl2sql.services import generate_sql_from_openrouter, execute_sql_query

def test_nlp_sql():
    prompt = "Show top 3 hiring companies for Data Scientists in Bengaluru with experience under 5 years"
    print(f"Testing Prompt: '{prompt}'...")
    
    try:
        sql, model = generate_sql_from_openrouter(prompt)
        print(f"Generated SQL (using {model}):\n{sql}\n")

        print("Executing generated query on Supabase PostgreSQL...")
        res = execute_sql_query(sql)
        print(f"Success! Returned {res['row_count']} rows in {res['execution_time_ms']} ms.")
        print("Columns:", res['columns'])
        print("First row:", res['rows'][0] if res['rows'] else "No rows")
    except Exception as e:
        print("Error during test:", e)

if __name__ == "__main__":
    test_nlp_sql()
