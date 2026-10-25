import unittest
from nl2sql.services import validate_sql, strip_sql_comments


class SQLValidationTestCase(unittest.TestCase):
    """
    Unit test suite verifying validate_sql hardening rules:
    a) comment stripping
    b) single-statement enforcement
    c) SELECT or WITH requirement
    d) dangerous keyword and function blocking
    e) strict 'indian_tech_jobs' table allowlist
    f) automatic LIMIT 500 appending
    """

    # 1. Valid SELECT
    def test_valid_select(self):
        sql = "SELECT job_title, salary_midpoint_lpa FROM indian_tech_jobs WHERE primary_city = 'Bangalore'"
        validated = validate_sql(sql)
        self.assertTrue(validated.startswith("SELECT job_title, salary_midpoint_lpa FROM indian_tech_jobs"))
        self.assertTrue(validated.endswith("LIMIT 500"))

    # 2. Valid SELECT with existing LIMIT
    def test_valid_select_existing_limit(self):
        sql = "SELECT job_title FROM indian_tech_jobs LIMIT 25"
        validated = validate_sql(sql)
        self.assertEqual(validated, "SELECT job_title FROM indian_tech_jobs LIMIT 25")
        self.assertNotIn("LIMIT 500", validated)

    # 3. Valid WITH CTE
    def test_valid_with_cte(self):
        sql = (
            "WITH high_paying AS ("
            "    SELECT company_name, AVG(salary_midpoint_lpa) AS avg_sal "
            "    FROM indian_tech_jobs "
            "    GROUP BY company_name"
            ") "
            "SELECT * FROM high_paying"
        )
        validated = validate_sql(sql)
        self.assertTrue(validated.startswith("WITH high_paying AS"))
        self.assertTrue(validated.endswith("LIMIT 500"))

    # 4. Valid WITH multiple CTEs
    def test_valid_with_multiple_ctes(self):
        sql = (
            "WITH c1 AS (SELECT * FROM indian_tech_jobs WHERE is_senior = TRUE), "
            "c2 AS (SELECT * FROM c1 WHERE work_mode = 'Remote') "
            "SELECT * FROM c2 LIMIT 10"
        )
        validated = validate_sql(sql)
        self.assertTrue(validated.endswith("LIMIT 10"))

    # 5. Lowercase variant
    def test_lowercase_variant(self):
        sql = "select job_title, company_name from indian_tech_jobs where work_mode = 'Remote'"
        validated = validate_sql(sql)
        self.assertTrue(validated.startswith("select job_title"))
        self.assertTrue(validated.endswith("LIMIT 500"))

    # 6. Uppercase variant
    def test_uppercase_variant(self):
        sql = "SELECT JOB_TITLE, COMPANY_NAME FROM INDIAN_TECH_JOBS WHERE SALARY_DISCLOSED = TRUE"
        validated = validate_sql(sql)
        self.assertTrue(validated.startswith("SELECT JOB_TITLE"))
        self.assertTrue(validated.endswith("LIMIT 500"))

    # 7. Public schema qualification
    def test_public_schema_qualification(self):
        sql = "SELECT * FROM public.indian_tech_jobs LIMIT 5"
        validated = validate_sql(sql)
        self.assertIn("public.indian_tech_jobs", validated)

    # 8. Quoted table identifier
    def test_quoted_table_identifier(self):
        sql = 'SELECT * FROM "indian_tech_jobs" LIMIT 5'
        validated = validate_sql(sql)
        self.assertIn('"indian_tech_jobs"', validated)

    # 9. Trailing semicolon allowed (single statement)
    def test_trailing_semicolon_allowed(self):
        sql = "SELECT * FROM indian_tech_jobs;"
        validated = validate_sql(sql)
        self.assertTrue(validated.endswith("LIMIT 500"))

    # 10. Harmless comments stripped
    def test_comment_stripping(self):
        sql = (
            "-- Find remote data science jobs\n"
            "SELECT job_title FROM indian_tech_jobs /* comment */ WHERE work_mode = 'Remote'"
        )
        validated = validate_sql(sql)
        self.assertNotIn("--", validated)
        self.assertNotIn("/*", validated)
        self.assertTrue(validated.endswith("LIMIT 500"))

    # 11. Multi-statement attack via semicolon
    def test_multi_statement_attack(self):
        sql = "SELECT * FROM indian_tech_jobs; DROP TABLE indian_tech_jobs;"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertIn("Multiple SQL statements", str(ctx.exception))

    # 12. Comment-hidden DROP attack (single-line comment)
    def test_comment_hidden_drop_single_line(self):
        sql = "SELECT * FROM indian_tech_jobs; --\nDROP TABLE indian_tech_jobs;"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        # Semicolon followed by DROP after comment stripping triggers multi-statement or keyword rejection
        self.assertTrue(
            "Multiple SQL statements" in str(ctx.exception)
            or "Disallowed keyword" in str(ctx.exception)
        )

    # 13. Comment-hidden DROP attack (multi-line comment)
    def test_comment_hidden_drop_multi_line(self):
        sql = "SELECT * FROM indian_tech_jobs; /* safe */ DROP TABLE indian_tech_jobs;"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertTrue(
            "Multiple SQL statements" in str(ctx.exception)
            or "Disallowed keyword" in str(ctx.exception)
        )

    # 14. Dangerous function: pg_sleep
    def test_pg_sleep_blocked(self):
        sql = "SELECT pg_sleep(5) FROM indian_tech_jobs"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertIn("Disallowed keyword or function", str(ctx.exception))

    # 15. Other table in FROM clause
    def test_other_table_from_blocked(self):
        sql = "SELECT * FROM auth_user"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertTrue(
            "must reference the 'indian_tech_jobs' table" in str(ctx.exception)
            or "Access to table" in str(ctx.exception)
        )

    # 16. Other table in JOIN clause
    def test_other_table_join_blocked(self):
        sql = "SELECT * FROM indian_tech_jobs JOIN sensitive_passwords ON 1=1"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertIn("Access to table 'sensitive_passwords' is not permitted", str(ctx.exception))

    # 17. Multiple tables in FROM (cross join)
    def test_multiple_tables_from_blocked(self):
        sql = "SELECT * FROM indian_tech_jobs, pg_catalog.pg_tables"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertTrue(
            "Access to table" in str(ctx.exception)
            or "Disallowed keyword" in str(ctx.exception)
        )

    # 18. Dangerous keyword: INSERT
    def test_disallowed_insert(self):
        sql = "INSERT INTO indian_tech_jobs (job_id) VALUES (1)"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertTrue(
            "Query must start with SELECT or WITH" in str(ctx.exception)
            or "Disallowed keyword" in str(ctx.exception)
        )

    # 19. Dangerous keyword: UPDATE
    def test_disallowed_update(self):
        sql = "UPDATE indian_tech_jobs SET job_title = 'test'"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertTrue(
            "Query must start with SELECT or WITH" in str(ctx.exception)
            or "Disallowed keyword" in str(ctx.exception)
        )

    # 20. Dangerous keyword: DELETE
    def test_disallowed_delete(self):
        sql = "DELETE FROM indian_tech_jobs"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertTrue(
            "Query must start with SELECT or WITH" in str(ctx.exception)
            or "Disallowed keyword" in str(ctx.exception)
        )

    # 21. Dangerous function: pg_read_file
    def test_pg_read_file_blocked(self):
        sql = "SELECT pg_read_file('/etc/passwd') FROM indian_tech_jobs"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertIn("Disallowed keyword or function", str(ctx.exception))

    # 22. Disallowed keyword: EXECUTE
    def test_execute_blocked(self):
        sql = "EXECUTE plan_run"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertTrue(
            "Query must start with SELECT or WITH" in str(ctx.exception)
            or "Disallowed keyword" in str(ctx.exception)
        )

    # 23. Disallowed metadata schema: information_schema
    def test_information_schema_blocked(self):
        sql = "SELECT * FROM information_schema.tables WHERE table_name = 'indian_tech_jobs'"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertTrue(
            "Disallowed keyword or function" in str(ctx.exception)
            or "Access to table" in str(ctx.exception)
        )

    # 24. String literal containing forbidden keyword is permitted inside quotes
    def test_keyword_inside_string_literal_permitted(self):
        sql = "SELECT * FROM indian_tech_jobs WHERE skills_required ILIKE '%drop%' LIMIT 10"
        validated = validate_sql(sql)
        self.assertIn("%drop%", validated)

    # 25. Non-SELECT/WITH prefix blocked
    def test_non_select_with_blocked(self):
        sql = "SHOW ALL"
        with self.assertRaises(ValueError) as ctx:
            validate_sql(sql)
        self.assertIn("Query must start with SELECT or WITH", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
