CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.course_supply_2024 AS
WITH presencial AS (
    SELECT
        census_year,
        institution_id,
        course_id,
        MAX(course_name) AS course_name,
        MAX(cine_label_code) AS cine_label_code,
        MAX(cine_label_name) AS cine_label_name,
        teaching_modality,
        SUM(course_count) AS course_count,
        SUM(offered_seats) AS offered_seats,
        SUM(applications) AS applications,
        SUM(entrants) AS entrants,
        SUM(enrollments) AS enrollments,
        SUM(graduates) AS graduates,
        COUNT(*) AS source_row_count
    FROM staging.courses_2024
    WHERE dimension_type = 1
      AND academic_level = 1
    GROUP BY
        census_year,
        institution_id,
        course_id,
        teaching_modality
),
ead_students AS (
    SELECT
        census_year,
        institution_id,
        course_id,
        teaching_modality,
        SUM(entrants) AS entrants,
        SUM(enrollments) AS enrollments,
        SUM(graduates) AS graduates,
        COUNT(*) AS source_row_count
    FROM staging.courses_2024
    WHERE dimension_type = 2
      AND academic_level = 1
    GROUP BY
        census_year,
        institution_id,
        course_id,
        teaching_modality
),
ead_capacity AS (
    SELECT
        census_year,
        institution_id,
        course_id,
        MAX(course_name) AS course_name,
        MAX(cine_label_code) AS cine_label_code,
        MAX(cine_label_name) AS cine_label_name,
        teaching_modality,
        SUM(course_count) AS course_count,
        SUM(offered_seats) AS offered_seats,
        SUM(applications) AS applications,
        COUNT(*) AS source_row_count
    FROM staging.courses_2024
    WHERE dimension_type = 3
      AND academic_level = 1
    GROUP BY
        census_year,
        institution_id,
        course_id,
        teaching_modality
),
ead AS (
    SELECT
        COALESCE(c.census_year, s.census_year) AS census_year,
        COALESCE(c.institution_id, s.institution_id) AS institution_id,
        COALESCE(c.course_id, s.course_id) AS course_id,
        c.course_name,
        c.cine_label_code,
        c.cine_label_name,
        COALESCE(c.teaching_modality, s.teaching_modality)
            AS teaching_modality,
        c.course_count,
        c.offered_seats,
        c.applications,
        s.entrants,
        s.enrollments,
        s.graduates,
        c.source_row_count AS capacity_source_row_count,
        s.source_row_count AS student_source_row_count
    FROM ead_capacity AS c
    FULL OUTER JOIN ead_students AS s
        USING (census_year, institution_id, course_id, teaching_modality)
)
SELECT
    census_year,
    institution_id,
    course_id,
    course_name,
    cine_label_code,
    cine_label_name,
    teaching_modality,
    course_count,
    offered_seats,
    applications,
    entrants,
    enrollments,
    graduates,
    source_row_count AS capacity_source_row_count,
    source_row_count AS student_source_row_count
FROM presencial

UNION ALL

SELECT
    census_year,
    institution_id,
    course_id,
    course_name,
    cine_label_code,
    cine_label_name,
    teaching_modality,
    course_count,
    offered_seats,
    applications,
    entrants,
    enrollments,
    graduates,
    capacity_source_row_count,
    student_source_row_count
FROM ead;

CREATE OR REPLACE VIEW analytics.course_sustainability_2024 AS
SELECT
    supply.*,
    institution.institution_name,
    institution.institution_abbreviation,
    institution.education_network,
    institution.administrative_category,
    institution.institution_state,
    entrants::NUMERIC / NULLIF(offered_seats, 0) AS seat_occupancy_rate,
    applications::NUMERIC / NULLIF(offered_seats, 0)
        AS applications_per_seat,
    offered_seats - entrants AS unconverted_seat_capacity,
    graduates::NUMERIC / NULLIF(enrollments, 0)
        AS graduation_intensity,
    offered_seats = 0 AS has_zero_offered_seats,
    entrants > offered_seats AND offered_seats > 0
        AS entrants_exceed_offered_seats,
    capacity_source_row_count IS NULL AS missing_capacity_component,
    student_source_row_count IS NULL AS missing_student_component
FROM analytics.course_supply_2024 AS supply
LEFT JOIN staging.institutions_2024 AS institution
    USING (census_year, institution_id);

