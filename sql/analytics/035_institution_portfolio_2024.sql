CREATE OR REPLACE VIEW analytics.institution_portfolio_2024 AS
WITH course_enrollments AS (
    SELECT
        census_year,
        institution_id,
        course_id,
        SUM(enrollments) AS enrollments
    FROM analytics.course_supply_2024
    GROUP BY census_year, institution_id, course_id
),
shares AS (
    SELECT
        course_enrollments.*,
        SUM(enrollments) OVER (
            PARTITION BY census_year, institution_id
        ) AS institution_enrollments,
        COUNT(*) OVER (
            PARTITION BY census_year, institution_id
        ) AS course_count
    FROM course_enrollments
)
SELECT
    census_year,
    institution_id,
    MAX(institution_enrollments) AS enrollments,
    MAX(course_count) AS course_count,
    SUM(
        POWER(
            enrollments::NUMERIC / NULLIF(institution_enrollments, 0),
            2
        )
    ) AS enrollment_hhi
FROM shares
GROUP BY census_year, institution_id;
