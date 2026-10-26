-- ============================================================================
-- India Tech Jobs 2026: Market Insights & Analysis SQL Queries
-- Database Engine: PostgreSQL (Supabase)
-- Target Table: indian_tech_jobs
-- ============================================================================

-- 1. Salary by domain with sample size (disclosed salaries only)
SELECT 
    skill_domain, 
    ROUND(AVG(salary_midpoint_lpa)::numeric, 1) AS avg_lpa, 
    COUNT(*) AS n
FROM indian_tech_jobs 
WHERE salary_midpoint_lpa > 0
GROUP BY 1 
ORDER BY 2 DESC;


-- 2. Work mode split with percentage
SELECT 
    work_mode, 
    COUNT(*) AS jobs,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM indian_tech_jobs 
GROUP BY 1 
ORDER BY 2 DESC;


-- 3. Jobs by primary_city (top 30 locations)
SELECT 
    primary_city, 
    COUNT(*) AS jobs 
FROM indian_tech_jobs 
GROUP BY 1 
ORDER BY 2 DESC 
LIMIT 30;


-- 4. Top 10 skills (split skills_required by comma, exclude 'Not Available')
SELECT 
    TRIM(skill) AS skill, 
    COUNT(*) AS jobs
FROM indian_tech_jobs, 
     UNNEST(string_to_array(skills_required, ',')) AS skill
WHERE skills_required <> 'Not Available'
GROUP BY 1 
ORDER BY 2 DESC 
LIMIT 10;


-- 5. Analyst roles by city with n_disclosed, fresher_roles and fresher average LPA (HAVING COUNT(*) >= 100)
SELECT 
    primary_city, 
    COUNT(*) AS jobs,
    COUNT(*) FILTER (WHERE salary_midpoint_lpa > 0) AS n_disclosed,
    COUNT(*) FILTER (WHERE is_fresher_friendly) AS fresher_roles,
    ROUND(AVG(CASE WHEN is_fresher_friendly AND salary_midpoint_lpa > 0 THEN salary_midpoint_lpa END)::numeric, 1) AS fresher_avg_lpa
FROM indian_tech_jobs
WHERE job_title ILIKE '%data analyst%' OR job_title ILIKE '%business analyst%'
GROUP BY 1 
HAVING COUNT(*) >= 100
ORDER BY 2 DESC;


-- 6. BI tool demand (Power BI, Tableau, Excel, MS Excel, Advanced Excel, SQL, Python)
SELECT 
    tool,
    COUNT(*) AS jobs
FROM (
    SELECT 'Power BI' AS tool FROM indian_tech_jobs WHERE skills_required ILIKE '%Power BI%'
    UNION ALL
    SELECT 'Tableau' AS tool FROM indian_tech_jobs WHERE skills_required ILIKE '%Tableau%'
    UNION ALL
    SELECT 'Excel' AS tool FROM indian_tech_jobs WHERE skills_required ILIKE '%Excel%'
    UNION ALL
    SELECT 'MS Excel' AS tool FROM indian_tech_jobs WHERE skills_required ILIKE '%MS Excel%'
    UNION ALL
    SELECT 'Advanced Excel' AS tool FROM indian_tech_jobs WHERE skills_required ILIKE '%Advanced Excel%'
    UNION ALL
    SELECT 'SQL' AS tool FROM indian_tech_jobs WHERE skills_required ILIKE '%SQL%'
    UNION ALL
    SELECT 'Python' AS tool FROM indian_tech_jobs WHERE skills_required ILIKE '%Python%'
) sub
GROUP BY tool
ORDER BY jobs DESC;


-- 7. SQL View jobs_clean mapping unnormalized city variants
-- Maps Pune% -> Pune, Mumbai% -> Mumbai, Bengaluru%/Bangalore% -> Bangalore, Hyderabad%/Secunderabad% -> Hyderabad
-- Keeps Remote as its own value and leaves everything else unchanged.
CREATE OR REPLACE VIEW jobs_clean AS
SELECT 
    *,
    CASE 
        WHEN primary_city ILIKE 'Pune%' THEN 'Pune'
        WHEN primary_city ILIKE 'Mumbai%' THEN 'Mumbai'
        WHEN primary_city ILIKE 'Bengaluru%' OR primary_city ILIKE 'Bangalore%' THEN 'Bangalore'
        WHEN primary_city ILIKE 'Hyderabad%' OR primary_city ILIKE 'Secunderabad%' THEN 'Hyderabad'
        ELSE primary_city
    END AS primary_city_clean
FROM indian_tech_jobs;


-- 8. City-cleanup preview query (inspecting cleaned city distribution)
SELECT 
    primary_city_clean,
    COUNT(*) AS total_jobs,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM jobs_clean
GROUP BY primary_city_clean
ORDER BY total_jobs DESC
LIMIT 15;
