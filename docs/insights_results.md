# India Tech Jobs 2026: Insights & Query Results

All queries below are mapped to [docs/insights.sql](file:///c:/Users/Acer/Desktop/SQL%20NLP/docs/insights.sql) and executed against the Supabase PostgreSQL database table `indian_tech_jobs`.

---

## 1. Salary by Domain with Sample Size (Disclosed Salaries Only)

### Query
```sql
SELECT 
    skill_domain, 
    ROUND(AVG(salary_midpoint_lpa)::numeric, 1) AS avg_lpa, 
    COUNT(*) AS n
FROM indian_tech_jobs 
WHERE salary_midpoint_lpa > 0
GROUP BY 1 
ORDER BY 2 DESC;
```

### Result
| skill_domain | avg_lpa | n |
| :--- | :---: | :---: |
| **Cloud & DevOps** | 19.0 | 367 |
| **AI/ML/DL** | 18.3 | 784 |
| **Data Engineering** | 17.2 | 184 |
| **Data Science** | 13.8 | 204 |
| **Business Intelligence** | 12.3 | 1,227 |

*Note: The spread between the highest-paying domain (Cloud & DevOps at 19.0 LPA) and the lowest (Business Intelligence at 12.3 LPA) is 6.7 LPA.*

---

## 2. Work Mode Split with Percentage

### Query
```sql
SELECT 
    work_mode, 
    COUNT(*) AS jobs,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM indian_tech_jobs 
GROUP BY 1 
ORDER BY 2 DESC;
```

### Result
| work_mode | jobs | pct (%) |
| :--- | :---: | :---: |
| **On-site** | 18,701 | 80.6% |
| **Hybrid** | 2,347 | 10.1% |
| **Remote** | 2,153 | 9.3% |

*Note: On-site work represents over 80% of hiring demand across indexed postings.*

---

## 3. Jobs by Primary City (Top 30 Locations)

### Query
```sql
SELECT 
    primary_city, 
    COUNT(*) AS jobs 
FROM indian_tech_jobs 
GROUP BY 1 
ORDER BY 2 DESC 
LIMIT 30;
```

### Result
| Rank | primary_city | jobs |
| :---: | :--- | :---: |
| 1 | **Mumbai** | 3,276 |
| 2 | **Bangalore** | 2,830 |
| 3 | **Chennai** | 2,666 |
| 4 | **Pune** | 2,606 |
| 5 | **Noida** | 2,585 |
| 6 | **Gurgaon** | 2,210 |
| 7 | **Remote** | 2,010 |
| 8 | **Kolkata** | 1,735 |
| 9 | **Ahmedabad** | 1,352 |
| 10 | **Delhi** | 920 |
| 11 | **Hyderabad** | 538 |
| 12 | **Hubli** | 38 |
| 13 | **Mumbai Suburban** | 33 |
| 14 | **Pune(Baner)** | 22 |
| 15 | **Panipat** | 19 |
| 16 | **Pune(Hinjewadi Phase 1)** | 11 |
| 17 | **Prayagraj** | 10 |
| 18 | **Indore** | 9 |
| 19 | **Kochi** | 9 |
| 20 | **Bhubaneswar** | 8 |
| 21 | **Pune(Kharadi)** | 7 |
| 22 | **Pune(Viman Nagar)** | 7 |
| 23 | **Mumbai(Airoli)** | 6 |
| 24 | **Kolkata(New Town)** | 6 |
| 25 | **Chennai(Perungudi)** | 6 |
| 26 | **Chennai(Guindy)** | 5 |
| 27 | **Pune(Kalyani Nagar)** | 5 |
| 28 | **Kolkata(Sector 5 Salt Lake)** | 5 |
| 29 | **Kolkata(Salt Lake)** | 5 |
| 30 | **Mumbai(Goregaon)** | 5 |

*Note: The top 5 locations (Mumbai, Bangalore, Chennai, Pune, Noida) account for 13,963 postings (60.2% of all listings). `primary_city` contains 198 distinct unnormalized variants.*

---

## 4. Top 10 Technical Skills

### Query
```sql
SELECT 
    TRIM(skill) AS skill, 
    COUNT(*) AS jobs
FROM indian_tech_jobs, 
     UNNEST(string_to_array(skills_required, ',')) AS skill
WHERE skills_required <> 'Not Available'
GROUP BY 1 
ORDER BY 2 DESC 
LIMIT 10;
```

### Result
| Rank | skill | jobs |
| :---: | :--- | :---: |
| 1 | **Python** | 2,744 |
| 2 | **Data analysis** | 2,360 |
| 3 | **Analytical** | 2,345 |
| 4 | **SQL** | 2,306 |
| 5 | **Automation** | 1,935 |
| 6 | **Machine learning** | 1,929 |
| 7 | **Artificial Intelligence** | 1,835 |
| 8 | **Computer science** | 1,687 |
| 9 | **Data** | 1,615 |
| 10 | **Analytics** | 1,567 |

---

## 5. Analyst Roles by City (Disclosed Sample, Fresher Count, and Fresher Average LPA)

### Query
```sql
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
```

### Result
| primary_city | jobs | n_disclosed | fresher_roles | fresher_avg_lpa |
| :--- | :---: | :---: | :---: | :---: |
| **Bangalore** | 774 | 61 | 133 | 4.4 LPA |
| **Pune** | 597 | 88 | 119 | 4.4 LPA |
| **Mumbai** | 576 | 85 | 110 | 5.1 LPA |
| **Chennai** | 454 | 72 | 83 | 9.0 LPA |
| **Gurgaon** | 288 | 35 | 77 | 9.7 LPA |
| **Delhi** | 252 | 38 | 58 | 4.0 LPA |
| **Noida** | 210 | 22 | 43 | 3.9 LPA |
| **Remote** | 170 | 31 | 43 | 7.3 LPA |
| **Ahmedabad** | 140 | 18 | 27 | 7.0 LPA |
| **Kolkata** | 130 | 19 | 36 | 5.2 LPA |
| **Hyderabad** | 103 | 36 | 13 | 12.2 LPA |

*Totals across these 11 locations: 3,694 jobs, 742 fresher-friendly roles (about 20%).*
*(Overall disclosed analyst salaries across all experience levels for comparison: Bangalore 11.4 LPA, Pune 14.8 LPA, Mumbai 11.7 LPA, Chennai 15.5 LPA, Gurgaon 12.0 LPA, Delhi 12.7 LPA, Noida 13.9 LPA, Remote 12.7 LPA, Ahmedabad 10.0 LPA, Kolkata 10.0 LPA, Hyderabad 16.4 LPA).*

---

## 6. Business Intelligence (BI) and Data Tool Demand

### Query
```sql
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
```

### Result
| Tool | Job Postings |
| :--- | :---: |
| **SQL** | 4,410 |
| **Python** | 4,351 |
| **Power BI** | 1,106 |
| **Excel** | 935 |
| **Tableau** | 350 |
| **Advanced Excel** | 229 |
| **MS Excel** | 18 |

---

## 7. SQL View: `jobs_clean`

### Query
```sql
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
```

---

## 8. City-Cleanup Preview (Cleaned City Distribution)

### Query
```sql
SELECT 
    primary_city_clean,
    COUNT(*) AS total_jobs,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM jobs_clean
GROUP BY primary_city_clean
ORDER BY total_jobs DESC
LIMIT 15;
```

### Result
| Rank | primary_city_clean | total_jobs | pct (%) |
| :---: | :--- | :---: | :---: |
| 1 | **Mumbai** | 3,382 | 14.58% |
| 2 | **Bangalore** | 2,830 | 12.20% |
| 3 | **Pune** | 2,692 | 11.60% |
| 4 | **Chennai** | 2,666 | 11.49% |
| 5 | **Noida** | 2,585 | 11.14% |
| 6 | **Gurgaon** | 2,210 | 9.53% |
| 7 | **Remote** | 2,010 | 8.66% |
| 8 | **Kolkata** | 1,735 | 7.48% |
| 9 | **Ahmedabad** | 1,352 | 5.83% |
| 10 | **Delhi** | 920 | 3.97% |
| 11 | **Hyderabad** | 539 | 2.32% |
| 12 | **Hubli** | 38 | 0.16% |
| 13 | **Panipat** | 19 | 0.08% |
| 14 | **Prayagraj** | 10 | 0.04% |
| 15 | **Indore** | 9 | 0.04% |

*Analysis: Normalizing locality patterns consolidates Mumbai from 3,276 to 3,382 (+106 jobs), Pune from 2,606 to 2,692 (+86 jobs), and Hyderabad from 538 to 539 jobs, while preserving Remote (2,010) as an independent location category.*
