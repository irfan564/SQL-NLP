# SQL-NLP Accuracy Evaluation Results

[FILL: run python evaluation/run_eval.py]

This evaluation suite tests 23 hand-verified natural-language questions from `evaluation/questions.json` across categories such as compensation (with undisclosed salary exclusions), remote work distribution, fresher opportunities, and skills.

To generate actual evaluation measurements, execute:
```bash
python evaluation/run_eval.py
```

The script will:
1. Translate each of the 23 questions into SQL using OpenRouter LLMs.
2. Execute the generated query against Supabase PostgreSQL under read-only safety rules.
3. Execute the hand-verified golden query and compare both result sets.
4. Record per-question latency, status (`CORRECT`, `INCORRECT`, `ERROR`), and write both `evaluation/results.csv` and an updated summary to this file.
