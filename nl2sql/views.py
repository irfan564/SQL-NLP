import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import connection
from .services import generate_sql_from_openrouter, execute_sql_query, validate_sql

CATEGORIZED_QUESTIONS = {
    "salary": [
        {"title": "Top Paying Companies", "prompt": "Top 5 companies with the highest average salary for Data Scientists"},
        {"title": "Highest Salary Tiers", "prompt": "Show top 10 job listings with salary midpoint greater than 30 LPA"},
        {"title": "Domain Compensation", "prompt": "Average salary midpoint LPA grouped by skill domain ordered by salary descending"},
        {"title": "Salary Disclosure by Skill Domain", "prompt": "Show percentage and count of jobs with disclosed salaries grouped by skill domain"}
    ],
    "remote": [
        {"title": "Remote AI/ML Roles", "prompt": "Show all remote jobs in AI/ML paying over 15 LPA"},
        {"title": "Work Mode Breakdown", "prompt": "Count of job postings grouped by work mode"},
        {"title": "City Remote Ratios", "prompt": "Count of remote jobs grouped by primary city"}
    ],
    "freshers": [
        {"title": "Fresher Friendly Companies", "prompt": "Top 5 companies hiring freshers with experience under 2 years"},
        {"title": "Entry Level AI Jobs", "prompt": "Show fresher friendly AI/ML engineer jobs in Bengaluru or Remote"},
        {"title": "Fresher Salary Range", "prompt": "Average salary for jobs with experience_min_yrs <= 1"},
        {"title": "Fresher Data & Business Analyst Roles by City", "prompt": "Count of fresher friendly data analyst and business analyst jobs grouped by primary city"}
    ],
    "skills": [
        {"title": "Python & SQL Demand", "prompt": "Find jobs requiring Python, SQL, and AWS in Bengaluru or Remote"},
        {"title": "Top Skill Domains", "prompt": "Total count of jobs grouped by skill domain"},
        {"title": "High Rating Tech MNCs", "prompt": "Highest rating companies hiring for Senior Data Engineers"}
    ]
}

DATASET_DOCS = [
    {"field": "job_title", "type": "Text", "desc": "Official position title advertised (e.g. Data Scientist, AI/ML Engineer, Full Stack Developer)."},
    {"field": "company_name", "type": "Text", "desc": "Hiring enterprise or recruiter organization (e.g. Google, Cisco, Wipro, TCS)."},
    {"field": "company_rating", "type": "Number (0-5)", "desc": "Employee feedback rating on a 5.0 scale."},
    {"field": "primary_city", "type": "Text", "desc": "Main Indian tech hub city (e.g. Bangalore, Hyderabad, Pune, Mumbai, Gurgaon, Noida, Chennai)."},
    {"field": "salary_midpoint_lpa", "type": "Number (LPA)", "desc": "Estimated mid-point annual package in Lakhs Per Annum (LPA)."},
    {"field": "experience_min_yrs", "type": "Number (Years)", "desc": "Minimum required professional experience in years."},
    {"field": "work_mode", "type": "Category", "desc": "Work model setup: On-site, Hybrid, or Remote."},
    {"field": "skill_domain", "type": "Category", "desc": "Technical domain focus (e.g. AI/ML/DL, Data Science, Business Intelligence, Software Engineering)."},
    {"field": "skills_required", "type": "Text Array", "desc": "List of required technical skills, languages, and frameworks."},
    {"field": "is_fresher_friendly", "type": "Boolean", "desc": "Indicates whether the role is suitable for freshers or 0-2 years experience."}
]

def index(request):
    """
    Renders the Corporate Data Portal with safe JSON data elements for charts.
    """
    summary = {
        "total_jobs": 23201,
        "avg_salary_lpa": 15.3,
        "salary_disclosed_pct": 11.9,
        "remote_pct": 9.3,
        "fresher_pct": 18.0,
    }
    
    cities = []
    domains = []
    work_modes = []

    city_chart = {"labels": ["Bangalore", "Hyderabad", "Pune", "Mumbai", "Gurgaon"], "values": [8450, 4210, 3890, 2650, 2100]}
    workmode_chart = {"labels": ["On-site", "Hybrid", "Remote"], "values": [16500, 4540, 2161]}
    domain_salary_chart = {
        "labels": ["Cloud & DevOps (n=367)", "AI/ML/DL (n=784)", "Data Engineering (n=184)", "Data Science (n=204)", "Business Intelligence (n=1227)"],
        "values": [19.0, 18.3, 17.2, 13.8, 12.3]
    }

    try:
        with connection.cursor() as cursor:
            # Summary stats: overview KPI uses AVG(salary_midpoint_lpa) WHERE salary_midpoint_lpa > 0
            cursor.execute("""
                SELECT 
                    COUNT(*),
                    COALESCE(ROUND(AVG(CASE WHEN salary_midpoint_lpa > 0 THEN salary_midpoint_lpa END)::numeric, 1), 0),
                    ROUND(COUNT(CASE WHEN salary_midpoint_lpa > 0 THEN 1 END) * 100.0 / COUNT(*), 1),
                    ROUND(COUNT(CASE WHEN work_mode ILIKE '%remote%' THEN 1 END) * 100.0 / COUNT(*), 1),
                    ROUND(COUNT(CASE WHEN is_fresher_friendly = True THEN 1 END) * 100.0 / COUNT(*), 1)
                FROM indian_tech_jobs;
            """)
            row = cursor.fetchone()
            if row:
                summary["total_jobs"] = row[0]
                summary["avg_salary_lpa"] = float(row[1]) if row[1] else 0.0
                summary["salary_disclosed_pct"] = float(row[2]) if row[2] else 0.0
                summary["remote_pct"] = float(row[3]) if row[3] else 0.0
                summary["fresher_pct"] = float(row[4]) if row[4] else 0.0

            # Filter options
            cursor.execute("SELECT DISTINCT primary_city FROM indian_tech_jobs WHERE primary_city IS NOT NULL AND primary_city != '' ORDER BY primary_city LIMIT 30;")
            cities = [r[0] for r in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT skill_domain FROM indian_tech_jobs WHERE skill_domain IS NOT NULL AND skill_domain != '' ORDER BY skill_domain LIMIT 30;")
            domains = [r[0] for r in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT work_mode FROM indian_tech_jobs WHERE work_mode IS NOT NULL AND work_mode != '' ORDER BY work_mode;")
            work_modes = [r[0] for r in cursor.fetchall()]

            # Chart 1: Cities
            cursor.execute("""
                SELECT primary_city, COUNT(*) as cnt 
                FROM indian_tech_jobs 
                WHERE primary_city IS NOT NULL AND primary_city != ''
                GROUP BY primary_city ORDER BY cnt DESC LIMIT 5;
            """)
            city_rows = cursor.fetchall()
            if city_rows:
                city_chart["labels"] = [r[0] for r in city_rows]
                city_chart["values"] = [r[1] for r in city_rows]

            # Chart 2: Work Modes
            cursor.execute("""
                SELECT work_mode, COUNT(*) as cnt 
                FROM indian_tech_jobs 
                WHERE work_mode IS NOT NULL AND work_mode != ''
                GROUP BY work_mode ORDER BY cnt DESC;
            """)
            wm_rows = cursor.fetchall()
            if wm_rows:
                workmode_chart["labels"] = [r[0] for r in wm_rows]
                workmode_chart["values"] = [r[1] for r in wm_rows]

            # Chart 3: Domain Salaries (disclosed salaries only with sample sizes)
            cursor.execute("""
                SELECT skill_domain, ROUND(AVG(salary_midpoint_lpa)::numeric, 1) as avg_sal, COUNT(*) as n
                FROM indian_tech_jobs 
                WHERE skill_domain IS NOT NULL AND skill_domain != '' AND salary_midpoint_lpa > 0
                GROUP BY skill_domain ORDER BY avg_sal DESC LIMIT 5;
            """)
            ds_rows = cursor.fetchall()
            if ds_rows:
                domain_salary_chart["labels"] = [f"{r[0]} (n={r[2]})" for r in ds_rows]
                domain_salary_chart["values"] = [float(r[1]) for r in ds_rows]

    except Exception as e:
        print("Error fetching view stats:", e)

    context = {
        "summary": summary,
        "cities": cities,
        "domains": domains,
        "work_modes": work_modes,
        "categorized_questions": CATEGORIZED_QUESTIONS,
        "dataset_docs": DATASET_DOCS,
        "city_chart_json": json.dumps(city_chart),
        "workmode_chart_json": json.dumps(workmode_chart),
        "domain_salary_chart_json": json.dumps(domain_salary_chart)
    }
    return render(request, "index.html", context)


def api_dataset_browse(request):
    """
    AJAX Endpoint: Paginated dataset explorer with live search & multi-column filtering.
    """
    try:
        search = request.GET.get("search", "").strip()
        city = request.GET.get("city", "").strip()
        domain = request.GET.get("domain", "").strip()
        work_mode = request.GET.get("work_mode", "").strip()
        min_salary = request.GET.get("min_salary", "0").strip()
        page = int(request.GET.get("page", "1"))
        page_size = int(request.GET.get("page_size", "10"))

        where_clauses = ["1=1"]
        params = []

        if search:
            where_clauses.append("(job_title ILIKE %s OR company_name ILIKE %s OR skills_required ILIKE %s)")
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])

        if city:
            where_clauses.append("primary_city = %s")
            params.append(city)

        if domain:
            where_clauses.append("skill_domain = %s")
            params.append(domain)

        if work_mode:
            where_clauses.append("work_mode = %s")
            params.append(work_mode)

        if min_salary and min_salary != "0":
            try:
                val = float(min_salary)
                where_clauses.append("salary_midpoint_lpa >= %s")
                params.append(val)
            except ValueError:
                pass

        where_sql = " AND ".join(where_clauses)
        offset = (page - 1) * page_size

        with connection.cursor() as cursor:
            count_query = f"SELECT COUNT(*) FROM indian_tech_jobs WHERE {where_sql};"
            cursor.execute(count_query, params)
            total_matching = cursor.fetchone()[0]

            query = f"""
                SELECT 
                    job_id, job_title, company_name, company_rating, primary_city, 
                    skill_domain, salary_midpoint_lpa, experience_min_yrs, experience_max_yrs, 
                    work_mode, skills_required, job_url
                FROM indian_tech_jobs 
                WHERE {where_sql}
                ORDER BY job_id ASC
                LIMIT %s OFFSET %s;
            """
            cursor.execute(query, params + [page_size, offset])
            columns = [c[0] for c in cursor.description]
            rows = [list(r) for r in cursor.fetchall()]

        total_pages = max(1, (total_matching + page_size - 1) // page_size)

        return JsonResponse({
            "success": True,
            "page": page,
            "page_size": page_size,
            "total_records": total_matching,
            "total_pages": total_pages,
            "columns": columns,
            "rows": rows
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
def api_nl2sql(request):
    """
    Translates Natural Language prompt into SQL via OpenRouter,
    validates the SQL using validate_sql, executes read-only, and returns results.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid HTTP method. Only POST is allowed."}, status=405)

    try:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"success": False, "error": "Invalid JSON in request body."}, status=400)

        prompt = data.get("prompt", "").strip()
        if not prompt:
            return JsonResponse({"success": False, "error": "Please provide a natural language prompt."}, status=400)

        raw_sql, model_used = generate_sql_from_openrouter(prompt)
        validated_sql = validate_sql(raw_sql)
        result = execute_sql_query(validated_sql)

        return JsonResponse({
            "success": True,
            "prompt": prompt,
            "sql": result.get("executed_sql", validated_sql),
            "model": model_used,
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
            "execution_time_ms": result["execution_time_ms"],
            "chart_data": result["chart_data"]
        })

    except ValueError as ve:
        return JsonResponse({"success": False, "error": str(ve)}, status=400)
    except Exception:
        return JsonResponse({"success": False, "error": "A database error occurred while executing the query."}, status=500)


@csrf_exempt
def api_run_sql(request):
    """
    Executes raw SQL query after validation.
    Guarded by ENABLE_RAW_SQL setting (default False -> returns 403 Forbidden).
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid HTTP method. Only POST is allowed."}, status=405)

    if not getattr(settings, "ENABLE_RAW_SQL", False):
        return JsonResponse({
            "success": False,
            "error": "Raw SQL execution is disabled. Set ENABLE_RAW_SQL=True in .env to enable."
        }, status=403)

    try:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"success": False, "error": "Invalid JSON in request body."}, status=400)

        sql_input = data.get("sql", "").strip() or data.get("custom_sql", "").strip()
        if not sql_input:
            return JsonResponse({"success": False, "error": "Please provide a SQL query."}, status=400)

        validated_sql = validate_sql(sql_input)
        result = execute_sql_query(validated_sql)

        return JsonResponse({
            "success": True,
            "sql": result.get("executed_sql", validated_sql),
            "model": "Raw SQL",
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
            "execution_time_ms": result["execution_time_ms"],
            "chart_data": result["chart_data"]
        })

    except ValueError as ve:
        return JsonResponse({"success": False, "error": str(ve)}, status=400)
    except Exception:
        return JsonResponse({"success": False, "error": "A database error occurred while executing the query."}, status=500)


@csrf_exempt
def api_generate_and_execute(request):
    """
    Backward-compatible unified endpoint.
    Delegates to api_run_sql if custom_sql is provided, or api_nl2sql if prompt is provided.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid HTTP method. Only POST is allowed."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"success": False, "error": "Invalid JSON in request body."}, status=400)

    if data.get("custom_sql"):
        return api_run_sql(request)
    return api_nl2sql(request)


def api_schema(request):
    """
    Returns column details and table stats for the Supabase schema inspector.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'indian_tech_jobs'
                ORDER BY ordinal_position;
            """)
            columns = [{"name": row[0], "type": row[1]} for row in cursor.fetchall()]

            cursor.execute("SELECT COUNT(*) FROM indian_tech_jobs;")
            total_jobs = cursor.fetchone()[0]

        return JsonResponse({
            "success": True,
            "table": "indian_tech_jobs",
            "total_rows": total_jobs,
            "columns": columns
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
