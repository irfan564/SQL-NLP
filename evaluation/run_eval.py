"""
Accuracy Evaluation Script for SQL-NLP

Evaluates NL2SQL translation accuracy by:
1. Loading 20 hand-verified golden questions from evaluation/questions.json.
2. Generating SQL queries via the OpenRouter LLM pipeline.
3. Executing both the generated SQL and the golden SQL against Supabase PostgreSQL.
4. Comparing the resulting datasets (ignoring column aliases and row order).
5. Outputting detailed results to evaluation/results.csv and summary to evaluation/RESULTS.md.

Usage:
    python evaluation/run_eval.py
"""

import os
import sys
import json
import csv
import time
from datetime import datetime
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sql_nlp_project.settings")

import django
django.setup()

from django.db import connection, transaction
from nl2sql.services import generate_sql_from_openrouter, execute_sql_query


def normalize_cell(val):
    """Normalizes cell values for order-independent, alias-independent set comparison."""
    if val is None:
        return "NULL"
    if isinstance(val, float):
        return str(round(val, 2))
    if isinstance(val, int):
        return str(val)
    if isinstance(val, bool):
        return str(val).lower()
    return str(val).strip().lower()


def normalize_rows(rows):
    """Sorts and normalizes rows into comparable tuples."""
    if not rows:
        return []
    normalized = []
    for row in rows:
        normalized.append(tuple(normalize_cell(c) for c in row))
    return sorted(normalized)


def execute_golden_query(golden_sql):
    """Executes the hand-verified golden SQL query."""
    with transaction.atomic():
        with connection.cursor() as cursor:
            if connection.vendor == "postgresql":
                cursor.execute("SET LOCAL TRANSACTION READ ONLY;")
                cursor.execute("SET LOCAL statement_timeout = '5s';")
            cursor.execute(golden_sql)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = [list(r) for r in cursor.fetchall()]
            return columns, rows


def run_evaluation():
    questions_file = BASE_DIR / "evaluation" / "questions.json"
    results_csv_file = BASE_DIR / "evaluation" / "results.csv"
    results_md_file = BASE_DIR / "evaluation" / "RESULTS.md"

    if not questions_file.exists():
        print(f"Error: {questions_file} not found.")
        sys.exit(1)

    with open(questions_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} evaluation questions. Running live pipeline...")

    records = []
    total = len(questions)
    correct_count = 0
    incorrect_count = 0
    error_count = 0
    failed_questions = []

    for item in questions:
        q_id = item["id"]
        category = item.get("category", "general")
        question = item["question"]
        golden_sql = item["golden_sql"]

        print(f"\n[{q_id}/{total}] Evaluating: {question}")

        generated_sql = ""
        model_used = "N/A"
        status = "ERROR"
        err_msg = ""
        exec_time_ms = 0.0

        # Step 1: Run Golden Query
        try:
            _, golden_rows = execute_golden_query(golden_sql)
            norm_golden = normalize_rows(golden_rows)
        except Exception as e:
            err_msg = f"Golden query error: {str(e)}"
            print(f"  ❌ {err_msg}")
            error_count += 1
            records.append({
                "id": q_id,
                "category": category,
                "question": question,
                "golden_sql": golden_sql,
                "generated_sql": "",
                "model": "N/A",
                "status": "ERROR",
                "execution_time_ms": 0,
                "error_message": err_msg
            })
            failed_questions.append((q_id, question, err_msg, golden_sql, ""))
            continue

        # Step 2: Generate SQL via OpenRouter
        try:
            t0 = time.time()
            generated_sql, model_used = generate_sql_from_openrouter(question)
            gen_duration = (time.time() - t0) * 1000
        except Exception as e:
            err_msg = f"LLM generation failed: {str(e)}"
            print(f"  ❌ {err_msg}")
            error_count += 1
            records.append({
                "id": q_id,
                "category": category,
                "question": question,
                "golden_sql": golden_sql,
                "generated_sql": "",
                "model": model_used,
                "status": "ERROR",
                "execution_time_ms": round(gen_duration if 'gen_duration' in locals() else 0, 2),
                "error_message": err_msg
            })
            failed_questions.append((q_id, question, err_msg, golden_sql, ""))
            continue

        # Step 3: Execute & Compare Generated SQL
        try:
            res = execute_sql_query(generated_sql)
            exec_time_ms = res.get("execution_time_ms", 0.0)
            norm_gen = normalize_rows(res.get("rows", []))

            if norm_golden == norm_gen:
                status = "CORRECT"
                correct_count += 1
                print(f"  ✅ CORRECT ({model_used}, {exec_time_ms} ms)")
            else:
                status = "INCORRECT"
                incorrect_count += 1
                err_msg = f"Result sets differ: golden returned {len(norm_golden)} rows, generated returned {len(norm_gen)} rows."
                print(f"  ⚠️ INCORRECT: {err_msg}")
                failed_questions.append((q_id, question, err_msg, golden_sql, generated_sql))

        except Exception as e:
            status = "ERROR"
            error_count += 1
            err_msg = f"Execution/Validation error: {str(e)}"
            print(f"  ❌ {err_msg}")
            failed_questions.append((q_id, question, err_msg, golden_sql, generated_sql))

        records.append({
            "id": q_id,
            "category": category,
            "question": question,
            "golden_sql": golden_sql,
            "generated_sql": generated_sql,
            "model": model_used,
            "status": status,
            "execution_time_ms": exec_time_ms,
            "error_message": err_msg
        })

    # Write CSV
    with open(results_csv_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "category", "question", "golden_sql", "generated_sql", "model", "status", "execution_time_ms", "error_message"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    accuracy_pct = round((correct_count / total) * 100, 1) if total > 0 else 0.0

    # Write RESULTS.md
    with open(results_md_file, "w", encoding="utf-8") as f:
        f.write("# SQL-NLP Accuracy Evaluation Results\n\n")
        f.write(f"- **Evaluated On:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"- **Total Questions:** {total}\n")
        f.write(f"- **Correct:** {correct_count} ({accuracy_pct}%)\n")
        f.write(f"- **Incorrect (Result Mismatch):** {incorrect_count}\n")
        f.write(f"- **Errors (Syntax/Validation/API):** {error_count}\n\n")

        f.write("## Detailed Results by Question\n\n")
        f.write("| ID | Category | Question | Status | Model | Latency (ms) |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in records:
            status_badge = "✅ CORRECT" if r["status"] == "CORRECT" else ("⚠️ INCORRECT" if r["status"] == "INCORRECT" else "❌ ERROR")
            f.write(f"| {r['id']} | {r['category']} | {r['question']} | {status_badge} | `{r['model']}` | {r['execution_time_ms']} |\n")

        if failed_questions:
            f.write("\n## Failed Questions Analysis\n\n")
            for q_id, q_text, reason, g_sql, gen_sql in failed_questions:
                f.write(f"### Q{q_id}: {q_text}\n\n")
                f.write(f"- **Outcome:** {reason}\n")
                f.write(f"- **Golden SQL:**\n```sql\n{g_sql}\n```\n")
                if gen_sql:
                    f.write(f"- **Generated SQL:**\n```sql\n{gen_sql}\n```\n")
                f.write("\n---\n\n")

    print(f"\n==========================================")
    print(f"Evaluation complete:")
    print(f"Total: {total} | Correct: {correct_count} ({accuracy_pct}%) | Incorrect: {incorrect_count} | Errors: {error_count}")
    print(f"Saved: {results_csv_file}")
    print(f"Saved: {results_md_file}")
    print(f"==========================================")


if __name__ == "__main__":
    run_evaluation()
