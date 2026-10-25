import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sql_nlp_project.settings')
import django
django.setup()

from nl2sql.services import generate_sql_from_openrouter, execute_sql_query

prompts = [
    "Top 5 hiring companies by total job count",
    "Average salary midpoint LPA by skill domain",
    "Show remote jobs in Data Science paying over 15 LPA"
]

for p in prompts:
    print(f"\n--- Prompt: '{p}' ---")
    try:
        sql, model = generate_sql_from_openrouter(p)
        print(f"Generated SQL ({model}):\n{sql}")
        res = execute_sql_query(sql)
        print(f"Returned {res['row_count']} rows in {res['execution_time_ms']} ms.")
        if res['rows']:
            print("Sample Row:", res['rows'][0])
        if res['chart_data']:
            print("Chart Data detected:", res['chart_data']['label_column'], "->", res['chart_data']['value_column'])
    except Exception as e:
        print(f"Error processing prompt: {e}")
