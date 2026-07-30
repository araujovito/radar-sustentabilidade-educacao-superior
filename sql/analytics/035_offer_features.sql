CREATE SCHEMA IF NOT EXISTS analytics;

-- Atributos por oferta e ano de referência, sem vazamento temporal.
--
-- Regra absoluta desta camada: uma linha com reference_year = t só pode conter
-- informação dos anos menores ou iguais a t. As métricas de
-- analytics.course_persistence NÃO podem ser usadas aqui — elas resumem a
-- série inteira, inclusive anos posteriores a cada observação, e serviriam
-- como vazamento direto do futuro.
--
-- A ausência de vazamento é garantida por construção: todas as janelas usam
-- ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW sobre census_year
-- ascendente, o que exclui qualquer linha posterior. As asserções em
-- sql/quality/044_assertions_features.sql verificam a propriedade recomputando
-- os atributos sobre a série truncada.
--
-- Defasagens usam aritmética de ano explícita, não LAG: a série tem lacunas e
-- LAG devolveria a linha observada anterior, que pode estar a vários anos.

CREATE OR REPLACE VIEW analytics.offer_features AS
WITH panel AS (
    SELECT
        institution_id,
        course_id,
        teaching_modality,
        census_year,
        education_network,
        administrative_category,
        offered_seats,
        applications,
        entrants,
        enrollments,
        graduates,
        entrants::NUMERIC / NULLIF(offered_seats, 0) AS occupancy_rate,
        -- Ocupação só é mensurável com capacidade declarada positiva. Ofertas
        -- sem capacidade não são ociosas: são não mensuráveis. O mesmo
        -- critério usado em analytics.course_persistence.
        COALESCE(offered_seats > 0, FALSE) AS has_measurable_occupancy,
        COALESCE(
            offered_seats > 0 AND entrants::NUMERIC / offered_seats < 0.25,
            FALSE
        ) AS is_low_occupancy
    FROM analytics.course_supply_snapshot
),
-- Ordinal da observação entre as mensuráveis da própria oferta. Depende
-- apenas de linhas com ano menor ou igual ao corrente.
ranked AS (
    SELECT
        panel.*,
        COUNT(*) FILTER (WHERE has_measurable_occupancy) OVER offer_to_date
            AS measurable_years_to_date,
        COUNT(*) OVER offer_to_date AS years_observed_to_date
    FROM panel
    WINDOW offer_to_date AS (
        PARTITION BY institution_id, course_id, teaching_modality
        ORDER BY census_year
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )
),
cumulative AS (
    SELECT
        ranked.*,
        COUNT(*) FILTER (WHERE is_low_occupancy) OVER offer_to_date
            AS low_occupancy_years_to_date,
        AVG(occupancy_rate) FILTER (WHERE has_measurable_occupancy)
            OVER offer_to_date AS mean_occupancy_to_date,
        STDDEV_SAMP(entrants::NUMERIC) OVER offer_to_date
            AS entrants_stddev_to_date,
        AVG(entrants::NUMERIC) OVER offer_to_date AS mean_entrants_to_date,
        -- Ordinal mensurável da última observação com ocupação aceitável.
        -- Permite contar a sequência ociosa corrente sem olhar adiante.
        MAX(measurable_years_to_date) FILTER (
            WHERE has_measurable_occupancy AND NOT is_low_occupancy
        ) OVER offer_to_date AS last_acceptable_ordinal
    FROM ranked
    WINDOW offer_to_date AS (
        PARTITION BY institution_id, course_id, teaching_modality
        ORDER BY census_year
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )
),
-- Concentração do portfólio da instituição no próprio ano de referência.
-- Usa apenas o ano t, portanto não olha adiante.
institution_shares AS (
    SELECT
        institution_id,
        census_year,
        enrollments::NUMERIC / NULLIF(
            SUM(enrollments) OVER (PARTITION BY institution_id, census_year),
            0
        ) AS enrollment_share
    FROM analytics.course_supply_snapshot
),
institution_year AS (
    SELECT
        institution_id,
        census_year,
        COUNT(*) AS institution_offer_count,
        SUM(POWER(enrollment_share, 2)) AS institution_enrollment_hhi
    FROM institution_shares
    GROUP BY institution_id, census_year
)
SELECT
    current_year.institution_id,
    current_year.course_id,
    current_year.teaching_modality,
    current_year.census_year AS reference_year,

    -- Contexto estático da oferta.
    current_year.education_network,
    current_year.administrative_category,

    -- Nível no ano de referência.
    current_year.offered_seats,
    current_year.entrants,
    current_year.enrollments,
    current_year.occupancy_rate,
    current_year.has_measurable_occupancy,
    current_year.applications::NUMERIC
        / NULLIF(current_year.offered_seats, 0) AS applications_per_seat,
    current_year.graduates::NUMERIC
        / NULLIF(current_year.enrollments, 0) AS graduation_intensity,

    -- Histórico acumulado até o ano de referência.
    current_year.years_observed_to_date,
    current_year.measurable_years_to_date,
    current_year.low_occupancy_years_to_date,
    current_year.low_occupancy_years_to_date::NUMERIC
        / NULLIF(current_year.measurable_years_to_date, 0)
        AS low_occupancy_share_to_date,
    current_year.measurable_years_to_date
        - COALESCE(current_year.last_acceptable_ordinal, 0)
        AS current_low_occupancy_streak,
    current_year.mean_occupancy_to_date,
    current_year.entrants_stddev_to_date
        / NULLIF(current_year.mean_entrants_to_date, 0)
        AS demand_volatility_to_date,

    -- Defasagens e variações, por aritmética de ano.
    previous_year.occupancy_rate AS occupancy_rate_lag1,
    current_year.occupancy_rate - previous_year.occupancy_rate
        AS occupancy_change_1y,
    current_year.enrollments::NUMERIC
        / NULLIF(previous_year.enrollments, 0) - 1 AS enrollment_growth_1y,
    current_year.offered_seats::NUMERIC
        / NULLIF(previous_year.offered_seats, 0) - 1 AS seat_growth_1y,
    current_year.enrollments::NUMERIC
        / NULLIF(two_years_before.enrollments, 0) - 1 AS enrollment_growth_2y,

    -- Contexto institucional no ano de referência.
    institution_year.institution_offer_count,
    institution_year.institution_enrollment_hhi
FROM cumulative AS current_year
LEFT JOIN cumulative AS previous_year
    ON previous_year.institution_id = current_year.institution_id
   AND previous_year.course_id = current_year.course_id
   AND previous_year.teaching_modality = current_year.teaching_modality
   AND previous_year.census_year = current_year.census_year - 1
LEFT JOIN cumulative AS two_years_before
    ON two_years_before.institution_id = current_year.institution_id
   AND two_years_before.course_id = current_year.course_id
   AND two_years_before.teaching_modality = current_year.teaching_modality
   AND two_years_before.census_year = current_year.census_year - 2
LEFT JOIN institution_year
    ON institution_year.institution_id = current_year.institution_id
   AND institution_year.census_year = current_year.census_year;
