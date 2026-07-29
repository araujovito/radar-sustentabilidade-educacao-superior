CREATE SCHEMA IF NOT EXISTS staging;

CREATE OR REPLACE VIEW staging.courses_2024 AS
SELECT
    NULLIF(TRIM(nu_ano_censo), '')::SMALLINT AS census_year,
    NULLIF(TRIM(tp_dimensao), '')::SMALLINT AS dimension_type,
    NULLIF(TRIM(co_regiao), '')::SMALLINT AS region_code,
    NULLIF(TRIM(co_uf), '')::SMALLINT AS state_code,
    NULLIF(TRIM(co_municipio), '')::INTEGER AS municipality_code,
    NULLIF(TRIM(co_ies), '')::INTEGER AS institution_id,
    NULLIF(TRIM(co_curso), '')::BIGINT AS course_id,
    NULLIF(TRIM(no_curso), '') AS course_name,
    NULLIF(TRIM(co_cine_rotulo), '') AS cine_label_code,
    NULLIF(TRIM(no_cine_rotulo), '') AS cine_label_name,
    NULLIF(TRIM(tp_modalidade_ensino), '')::SMALLINT AS teaching_modality,
    NULLIF(TRIM(tp_nivel_academico), '')::SMALLINT AS academic_level,
    NULLIF(TRIM(tp_grau_academico), '')::SMALLINT AS academic_degree,
    NULLIF(TRIM(qt_curso), '')::BIGINT AS course_count,
    NULLIF(TRIM(qt_vg_total), '')::BIGINT AS offered_seats,
    NULLIF(TRIM(qt_inscrito_total), '')::BIGINT AS applications,
    NULLIF(TRIM(qt_ing), '')::BIGINT AS entrants,
    NULLIF(TRIM(qt_mat), '')::BIGINT AS enrollments,
    NULLIF(TRIM(qt_conc), '')::BIGINT AS graduates
FROM raw.censo_superior_cursos_2024;

CREATE OR REPLACE VIEW staging.institutions_2024 AS
SELECT
    NULLIF(TRIM(nu_ano_censo), '')::SMALLINT AS census_year,
    NULLIF(TRIM(co_ies), '')::INTEGER AS institution_id,
    NULLIF(TRIM(no_ies), '') AS institution_name,
    NULLIF(TRIM(sg_ies), '') AS institution_abbreviation,
    NULLIF(TRIM(tp_organizacao_academica), '')::SMALLINT
        AS academic_organization,
    NULLIF(TRIM(tp_rede), '')::SMALLINT AS education_network,
    NULLIF(TRIM(tp_categoria_administrativa), '')::SMALLINT
        AS administrative_category,
    NULLIF(TRIM(co_municipio_ies), '')::INTEGER
        AS institution_municipality_code,
    NULLIF(TRIM(sg_uf_ies), '') AS institution_state
FROM raw.censo_superior_ies_2024;

