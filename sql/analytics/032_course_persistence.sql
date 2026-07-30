CREATE SCHEMA IF NOT EXISTS analytics;

-- Persistência da capacidade ociosa e volatilidade da demanda (2014-2024).
--
-- A unidade do painel é a oferta: IES, curso e modalidade, observada ao longo
-- dos anos. Estas views são descritivas e retrospectivas — usam a série
-- inteira, inclusive anos posteriores a cada observação. Por isso NÃO servem
-- como atributos de um modelo preditivo, que exigirá recorte temporal e
-- construção sem informação futura (Marco 4).
--
-- Convenção de ociosidade: ocupação abaixo de 0,25. O valor fica abaixo da
-- ocupação ponderada das duas modalidades em 2024 (32,8% presencial e 18,0%
-- EAD), marcando conversão claramente fraca sem depender da modalidade. Os
-- componentes ficam expostos para que outro limiar possa ser recalculado.

CREATE OR REPLACE VIEW analytics.course_supply_panel AS
SELECT
    census_year,
    institution_id,
    course_id,
    teaching_modality,
    course_name,
    education_network,
    administrative_category,
    offered_seats,
    applications,
    entrants,
    enrollments,
    graduates,
    entrants::NUMERIC / NULLIF(offered_seats, 0) AS seat_occupancy_rate,
    -- A ocupação só é mensurável quando há capacidade declarada. Ofertas com
    -- zero vagas não são ociosas: são não mensuráveis, e contá-las como
    -- ociosas inflaria a persistência.
    offered_seats > 0 AS has_measurable_occupancy,
    offered_seats > 0
        AND entrants::NUMERIC / offered_seats < 0.25
        AS is_low_occupancy
-- Lê a materialização, não a view: reconstruir a união das onze edições a
-- cada consulta torna o painel inviável. Ver 033_materialize_supply.sql.
FROM analytics.course_supply_snapshot;

CREATE OR REPLACE VIEW analytics.course_persistence AS
WITH measurable AS (
    SELECT
        institution_id,
        course_id,
        teaching_modality,
        census_year,
        seat_occupancy_rate,
        is_low_occupancy,
        offered_seats,
        entrants
    FROM analytics.course_supply_panel
    WHERE has_measurable_occupancy
),
-- Conta os anos ociosos consecutivos mais recentes: percorre a série de trás
-- para frente e para no primeiro ano com ocupação aceitável.
recent_run AS (
    SELECT
        institution_id,
        course_id,
        teaching_modality,
        is_low_occupancy,
        SUM(CASE WHEN is_low_occupancy THEN 0 ELSE 1 END) OVER (
            PARTITION BY institution_id, course_id, teaching_modality
            ORDER BY census_year DESC
            ROWS UNBOUNDED PRECEDING
        ) AS acceptable_years_seen
    FROM measurable
),
streak AS (
    SELECT
        institution_id,
        course_id,
        teaching_modality,
        COUNT(*) FILTER (
            WHERE acceptable_years_seen = 0 AND is_low_occupancy
        ) AS current_low_occupancy_streak
    FROM recent_run
    GROUP BY institution_id, course_id, teaching_modality
),
aggregated AS (
    SELECT
        institution_id,
        course_id,
        teaching_modality,
        MIN(census_year) AS first_year,
        MAX(census_year) AS last_year,
        COUNT(*) AS measurable_years,
        COUNT(*) FILTER (WHERE is_low_occupancy) AS low_occupancy_years,
        AVG(seat_occupancy_rate) AS mean_occupancy_rate,
        STDDEV_SAMP(seat_occupancy_rate) AS occupancy_stddev,
        AVG(entrants::NUMERIC) AS mean_entrants,
        STDDEV_SAMP(entrants::NUMERIC) AS entrants_stddev,
        SUM(offered_seats - entrants) AS total_unconverted_capacity
    FROM measurable
    GROUP BY institution_id, course_id, teaching_modality
)
SELECT
    aggregated.institution_id,
    aggregated.course_id,
    aggregated.teaching_modality,
    aggregated.first_year,
    aggregated.last_year,
    aggregated.measurable_years,
    aggregated.low_occupancy_years,
    streak.current_low_occupancy_streak,
    aggregated.low_occupancy_years::NUMERIC
        / NULLIF(aggregated.measurable_years, 0) AS low_occupancy_share,
    aggregated.mean_occupancy_rate,
    aggregated.occupancy_stddev,
    aggregated.total_unconverted_capacity,
    -- Coeficiente de variação: desvio padrão relativo à média, comparável
    -- entre ofertas de escalas muito diferentes. Indefinido quando a média de
    -- ingressantes é zero.
    aggregated.entrants_stddev / NULLIF(aggregated.mean_entrants, 0)
        AS demand_volatility,
    -- A série tem lacunas: uma oferta pode desaparecer e voltar. Consumidores
    -- devem exigir um mínimo de anos antes de interpretar volatilidade.
    aggregated.last_year - aggregated.first_year + 1
        AS calendar_span,
    aggregated.measurable_years
        < (aggregated.last_year - aggregated.first_year + 1)
        AS has_gaps
FROM aggregated
JOIN streak
    USING (institution_id, course_id, teaching_modality);
