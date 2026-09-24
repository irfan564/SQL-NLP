import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
if not SUPABASE_DB_URL:
    print("Error: SUPABASE_DB_URL not found in .env")
    sys.exit(1)

CSV_FILE = "indian_tech_jobs_2026.csv"

def seed_database():
    print(f"Reading dataset: {CSV_FILE}...")
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found!")
        sys.exit(1)

    df = pd.read_csv(CSV_FILE)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

    # Clean boolean columns and numeric columns
    for col in ['salary_disclosed', 'is_senior', 'is_fresher_friendly', 'salary_negotiable']:
        if col in df.columns:
            df[col] = df[col].astype(bool)

    numeric_cols = [
        'company_rating', 'experience_min_yrs', 'experience_max_yrs',
        'salary_min_lpa', 'salary_max_lpa', 'skills_count',
        'salary_midpoint_lpa', 'days_since_posted'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    print("Connecting to Supabase PostgreSQL database...")
    engine = create_engine(SUPABASE_DB_URL, pool_pre_ping=True)

    print("Uploading data to Supabase table 'indian_tech_jobs'...")
    table_name = "indian_tech_jobs"
    # Seed using standard fast chunking
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=2000
    )

    print("Creating indexes on key columns for optimized query execution...")
    with engine.connect() as conn:
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_tech_jobs_title ON {table_name} (job_title);",
            f"CREATE INDEX IF NOT EXISTS idx_tech_jobs_company ON {table_name} (company_name);",
            f"CREATE INDEX IF NOT EXISTS idx_tech_jobs_city ON {table_name} (primary_city);",
            f"CREATE INDEX IF NOT EXISTS idx_tech_jobs_domain ON {table_name} (skill_domain);",
            f"CREATE INDEX IF NOT EXISTS idx_tech_jobs_salary ON {table_name} (salary_midpoint_lpa);",
            f"CREATE INDEX IF NOT EXISTS idx_tech_jobs_workmode ON {table_name} (work_mode);",
            f"CREATE INDEX IF NOT EXISTS idx_tech_jobs_exp ON {table_name} (experience_min_yrs);"
        ]
        for idx_sql in indexes:
            conn.execute(text(idx_sql))
        conn.commit()

    print(f"Successfully seeded {len(df)} records into Supabase 'indian_tech_jobs'!")

if __name__ == "__main__":
    seed_database()
