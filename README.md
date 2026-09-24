# India Tech Jobs 2026 — NL2SQL Analytics Portal

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2%2B-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![OpenRouter](https://img.shields.io/badge/AI-OpenRouter%20LLM-FF6B35?style=for-the-badge&logo=openai&logoColor=white)
![Chart.js](https://img.shields.io/badge/Charts-Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)

**An enterprise-grade analytics portal that translates plain English into live PostgreSQL queries — powered by OpenRouter LLMs and built on 23,201 Indian tech job records.**

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [Dataset](#-dataset) · [AI Engine](#-ai-engine)

</div>

---

## Features

| Feature | Description |
|---|---|
| NL to SQL Engine | Type any question in plain English and get live PostgreSQL results instantly |
| Interactive Charts | City hiring hubs, work-mode split (Remote/Hybrid/On-site), salary by domain |
| Dataset Explorer | Filter, search and paginate all 23,201 job records |
| Analysis Library | Pre-built question bank across Salary, Remote Work, Fresher Entry and Skills |
| Multi-LLM Fallback | Llama 3.3 70B then Claude 3.5 Sonnet then DeepSeek R1 then GPT-4o Mini |
| SQL Safety Guard | Server-side validation blocks all non-SELECT statements before execution |
| Auto Chart | Aggregate query results automatically rendered as a bar/pie chart |
| CSV Export | Export filtered explorer results with one click |

---

## Architecture

```
Browser (Frontend)
  Vanilla HTML + CSS (Plus Jakarta Sans) + Chart.js + Lucide Icons

        |  HTTP / REST
        v

Django 4.x Application Server
  nl2sql/views.py  -->  nl2sql/services.py
  (REST APIs)            generate_sql_from_openrouter()
                         execute_sql_query() [safe, read-only]

        |                        |
        v                        v
  OpenRouter API        Supabase PostgreSQL DB
  (LLM NL->SQL)         Table: indian_tech_jobs
  Llama / Claude /      23,201 rows x 26 columns
  DeepSeek / GPT-4o
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- A [Supabase](https://supabase.com) project with the dataset loaded
- An [OpenRouter](https://openrouter.ai) API key (free tier works)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/india-tech-jobs-nl2sql.git
cd india-tech-jobs-nl2sql
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
SUPABASE_DB_URL=postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
OPENROUTER_API_KEY=sk-or-v1-...
```

### 5. Seed the database (optional)

If you are connecting to an existing Supabase project that already has the `indian_tech_jobs` table, skip this step.

```bash
# Edit seed_supabase.py with your DB credentials, then run:
python seed_supabase.py
```

The SQL schema is available in `sql.sql`.

### 6. Run the development server

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## Dataset

The portal is powered by **23,201 Indian Tech Job listings** from 2026 with 26 structured columns:

| Column | Description |
|---|---|
| `job_title` | Position name (e.g., Data Scientist, AI/ML Engineer) |
| `company_name` | Hiring company |
| `primary_city` | Bangalore, Hyderabad, Pune, Mumbai, Delhi, etc. |
| `salary_midpoint_lpa` | Midpoint salary in Lakhs Per Annum |
| `work_mode` | On-site / Hybrid / Remote |
| `skill_domain` | AI/ML/DL, Data Science, Full Stack, DevOps, etc. |
| `skills_required` | Required tech skills comma-separated |
| `is_fresher_friendly` | Boolean — 0-2 yrs experience roles |
| `experience_min_yrs` | Minimum experience needed |
| `salary_tier` | Entry / Mid / Senior / Premium classification |

> **Note:** The raw CSV (`indian_tech_jobs_2026.csv`) is excluded from this repo via `.gitignore` due to its size (~14 MB). Use the Supabase database directly or download the dataset separately.

---

## AI Engine

The NL-to-SQL pipeline in `nl2sql/services.py` works as follows:

1. User types a plain English question
2. System prompt injects the full 26-column schema context plus strict PostgreSQL rules
3. OpenRouter API is called with a cascade of LLMs in priority order:
   - `meta-llama/llama-3.3-70b-instruct` (primary)
   - `anthropic/claude-3.5-sonnet` (fallback 1)
   - `deepseek/deepseek-r1` (fallback 2)
   - `openai/gpt-4o-mini` (fallback 3)
4. SQL is extracted from the code block in the LLM response
5. Safety validation blocks any non-SELECT keywords before execution
6. Query runs against Supabase PostgreSQL and results are returned as JSON
7. Auto chart detection — if results have a label + numeric column and 30 or fewer rows, a Chart.js visualization is offered

---

## Project Structure

```
india-tech-jobs-nl2sql/
|
|-- manage.py                    # Django entry point
|-- requirements.txt             # Python dependencies
|-- .env.example                 # Environment variable template
|-- sql.sql                      # Database schema DDL
|-- seed_supabase.py             # Script to seed Supabase from CSV
|
|-- sql_nlp_project/             # Django project config
|   |-- settings.py              # Settings (reads from .env)
|   |-- urls.py                  # Root URL routing
|   `-- wsgi.py
|
`-- nl2sql/                      # Main Django app
    |-- apps.py
    |-- views.py                 # All API + page view handlers
    |-- services.py              # NL->SQL engine + query executor
    |-- urls.py                  # App-level URL patterns
    |-- templates/
    |   `-- index.html           # Single-page analytics portal
    `-- static/
        `-- css/
            `-- style.css        # Custom enterprise UI styles
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Main analytics portal (HTML) |
| `POST` | `/api/nl2sql/` | Convert NL to SQL and execute |
| `POST` | `/api/run-sql/` | Execute custom SQL directly |
| `GET` | `/api/dataset-browse/` | Paginated, filtered dataset explorer |

### NL2SQL Request Example

```bash
curl -X POST http://localhost:8000/api/nl2sql/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Top 5 companies paying the highest average salary for Data Scientists"}'
```

---

## Requirements

```
django>=4.2,<6.0
psycopg2-binary>=2.9
dj-database-url>=2.1
requests>=2.31
python-dotenv>=1.0
pandas>=2.0
sqlalchemy>=2.0
```

---

## Security Notes

- All SQL is validated server-side — DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE, CREATE, GRANT, REVOKE are blocked
- `.env` is git-ignored — your keys are never committed
- Use a strong, unique `SECRET_KEY` in production
- Set `DEBUG=False` and configure `ALLOWED_HOSTS` for any public deployment

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the LICENSE file for details.

---

Built with Django, Supabase, OpenRouter, and Chart.js
