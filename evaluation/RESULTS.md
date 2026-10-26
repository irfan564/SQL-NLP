# SQL-NLP Accuracy Evaluation Results

- **Evaluated On:** 2026-10-26 06:16:58 UTC
- **Total Questions:** 23
- **Correct:** 16 (69.6%)
- **Incorrect (Result Mismatch):** 7
- **Errors (Syntax/Validation/API):** 0

## Detailed Results by Question

| ID | Category | Question | Status | Model | Latency (ms) |
|---|---|---|---|---|---|
| 1 | salary | What is the average salary midpoint LPA by skill domain? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 255.07 |
| 2 | remote | How many total job postings are there for each work mode? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 261.75 |
| 3 | companies | What are the top 5 hiring companies by total job postings? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 252.54 |
| 4 | freshers | What is the count of fresher-friendly roles grouped by primary city for the top 5 cities? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 257.44 |
| 5 | salary | What are the top 5 highest paying job titles by average salary midpoint? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 257.87 |
| 6 | remote | How many remote jobs require Python in their skills? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 282.99 |
| 7 | experience | What is the average minimum and maximum experience required for Data Scientist roles? | ⚠️ INCORRECT | `meta-llama/llama-3.3-70b-instruct` | 324.08 |
| 8 | cities | What are the top 5 cities with the highest number of tech job postings? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 250.79 |
| 9 | salary | How many jobs offer negotiable salaries versus non-negotiable? | ⚠️ INCORRECT | `meta-llama/llama-3.3-70b-instruct` | 264.82 |
| 10 | companies | What is the distribution of jobs across company size buckets? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 260.12 |
| 11 | companies | Show top 5 companies with the highest average rating having at least 10 job postings. | ⚠️ INCORRECT | `meta-llama/llama-3.3-70b-instruct` | 263.04 |
| 12 | salary | What percentage of jobs have salary disclosed? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 256.74 |
| 13 | salary | What is the average salary midpoint in Bangalore compared to Hyderabad and Pune? | ⚠️ INCORRECT | `meta-llama/llama-3.3-70b-instruct` | 310.16 |
| 14 | roles | How many jobs are categorized as senior roles? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 262.28 |
| 15 | skills | What are the top 5 skill domains by total number of postings? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 252.35 |
| 16 | skills | Show count of jobs requiring SQL grouped by experience tier. | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 303.59 |
| 17 | skills | What is the average number of skills required per job by work mode? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 261.14 |
| 18 | postings | How many job postings were posted within the last 7 days? | ⚠️ INCORRECT | `meta-llama/llama-3.3-70b-instruct` | 270.7 |
| 19 | remote | List top 5 companies offering Remote jobs in AI/ML/DL domain. | ⚠️ INCORRECT | `meta-llama/llama-3.3-70b-instruct` | 283.33 |
| 20 | freshers | What is the average salary midpoint for fresher-friendly vs non-fresher jobs? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 253.63 |
| 21 | salary | What is the average salary midpoint LPA for Machine Learning Engineers? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 256.29 |
| 22 | salary | What are the top 5 highest paying companies for Senior roles by average salary? | ✅ CORRECT | `meta-llama/llama-3.3-70b-instruct` | 261.53 |
| 23 | salary | What is the average salary midpoint LPA for remote roles versus on-site roles? | ⚠️ INCORRECT | `meta-llama/llama-3.3-70b-instruct` | 252.39 |

## Failed Questions Analysis

### Q7: What is the average minimum and maximum experience required for Data Scientist roles?

- **Outcome:** Result sets differ: golden returned 1 rows, generated returned 1 rows.
- **Golden SQL:**
```sql
SELECT ROUND(AVG(experience_min_yrs)::numeric, 2) AS avg_min_exp, ROUND(AVG(experience_max_yrs)::numeric, 2) AS avg_max_exp FROM indian_tech_jobs WHERE job_title ILIKE '%data scientist%';
```
- **Generated SQL:**
```sql
SELECT 
    round(AVG(experience_min_yrs)::numeric, 2) AS avg_min_experience,
    round(AVG(experience_max_yrs)::numeric, 2) AS avg_max_experience
FROM 
    indian_tech_jobs
WHERE 
    role_category ILIKE '%Data Scientist%'
LIMIT 100
```

---

### Q9: How many jobs offer negotiable salaries versus non-negotiable?

- **Outcome:** Result sets differ: golden returned 1 rows, generated returned 1 rows.
- **Golden SQL:**
```sql
SELECT salary_negotiable, COUNT(*) AS total_jobs FROM indian_tech_jobs GROUP BY salary_negotiable;
```
- **Generated SQL:**
```sql
SELECT 
    SUM(CASE WHEN salary_negotiable THEN 1 ELSE 0 END) AS negotiable_count,
    SUM(CASE WHEN NOT salary_negotiable THEN 1 ELSE 0 END) AS non_negotiable_count
FROM 
    indian_tech_jobs
LIMIT 100
```

---

### Q11: Show top 5 companies with the highest average rating having at least 10 job postings.

- **Outcome:** Result sets differ: golden returned 5 rows, generated returned 5 rows.
- **Golden SQL:**
```sql
SELECT company_name, ROUND(AVG(company_rating)::numeric, 2) AS avg_rating, COUNT(*) AS postings FROM indian_tech_jobs WHERE company_name IS NOT NULL AND company_name != '' AND company_rating > 0 GROUP BY company_name HAVING COUNT(*) >= 10 ORDER BY avg_rating DESC, postings DESC LIMIT 5;
```
- **Generated SQL:**
```sql
SELECT company_name, round(AVG(company_rating)::numeric, 2) as avg_rating
FROM indian_tech_jobs
GROUP BY company_name
HAVING COUNT(job_id) >= 10
ORDER BY avg_rating DESC
LIMIT 5
```

---

### Q13: What is the average salary midpoint in Bangalore compared to Hyderabad and Pune?

- **Outcome:** Result sets differ: golden returned 3 rows, generated returned 3 rows.
- **Golden SQL:**
```sql
SELECT primary_city, ROUND(AVG(salary_midpoint_lpa)::numeric, 2) AS avg_salary FROM indian_tech_jobs WHERE primary_city IN ('Bangalore', 'Hyderabad', 'Pune') AND salary_midpoint_lpa > 0 GROUP BY primary_city ORDER BY avg_salary DESC;
```
- **Generated SQL:**
```sql
SELECT 
    primary_city, 
    round(AVG(salary_midpoint_lpa)::numeric, 2) AS average_salary_midpoint
FROM 
    indian_tech_jobs
WHERE 
    salary_midpoint_lpa > 0
    AND primary_city ILIKE 'Bangalore' OR primary_city ILIKE 'Hyderabad' OR primary_city ILIKE 'Pune'
GROUP BY 
    primary_city
LIMIT 100
```

---

### Q18: How many job postings were posted within the last 7 days?

- **Outcome:** Result sets differ: golden returned 1 rows, generated returned 1 rows.
- **Golden SQL:**
```sql
SELECT COUNT(*) AS recent_jobs FROM indian_tech_jobs WHERE days_since_posted <= 7;
```
- **Generated SQL:**
```sql
SELECT COUNT(*) 
FROM indian_tech_jobs 
WHERE job_id IN (SELECT job_id FROM indian_tech_jobs ORDER BY job_id DESC LIMIT 100) 
AND job_id > (SELECT MAX(job_id) - 100 FROM indian_tech_jobs) 
LIMIT 100
```

---

### Q19: List top 5 companies offering Remote jobs in AI/ML/DL domain.

- **Outcome:** Result sets differ: golden returned 5 rows, generated returned 5 rows.
- **Golden SQL:**
```sql
SELECT company_name, COUNT(*) AS remote_roles FROM indian_tech_jobs WHERE work_mode ILIKE '%remote%' AND skill_domain ILIKE '%ai%ml%' AND company_name IS NOT NULL AND company_name != '' GROUP BY company_name ORDER BY remote_roles DESC LIMIT 5;
```
- **Generated SQL:**
```sql
SELECT company_name 
FROM indian_tech_jobs 
WHERE work_mode ILIKE 'Remote' AND skill_domain ILIKE 'AI/ML/DL'
GROUP BY company_name
ORDER BY COUNT(*) DESC
LIMIT 5
```

---

### Q23: What is the average salary midpoint LPA for remote roles versus on-site roles?

- **Outcome:** Result sets differ: golden returned 2 rows, generated returned 3 rows.
- **Golden SQL:**
```sql
-- Exclude undisclosed salaries
SELECT work_mode, ROUND(AVG(salary_midpoint_lpa)::numeric, 2) AS avg_salary FROM indian_tech_jobs WHERE work_mode IN ('Remote', 'On-site') AND salary_midpoint_lpa > 0 GROUP BY work_mode ORDER BY avg_salary DESC;
```
- **Generated SQL:**
```sql
SELECT 
    work_mode, 
    ROUND(AVG(salary_midpoint_lpa)::numeric, 2) AS average_salary_midpoint_lpa
FROM 
    indian_tech_jobs
WHERE 
    salary_midpoint_lpa > 0
GROUP BY 
    work_mode
```

---

