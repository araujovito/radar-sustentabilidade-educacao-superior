-- Transição entre modalidades e eficiência de conclusão com defasagem.
--
-- A comparação presencial/EAD usa IES × área CINE, não CO_CURSO. O código de
-- curso identifica uma oferta específica e não representa, necessariamente, o
-- mesmo produto nas duas modalidades.

CREATE TABLE IF NOT EXISTS analytics.modality_portfolio_state_snapshot AS
WITH portfolio AS (
    SELECT
        census_year,
        institution_id,
        cine_label_code,
        MAX(cine_label_name) AS cine_label_name,
        COUNT(*) FILTER (WHERE teaching_modality = 1)
            AS presencial_offers,
        COUNT(*) FILTER (WHERE teaching_modality = 2)
            AS ead_offers,
        COALESCE(
            SUM(offered_seats) FILTER (WHERE teaching_modality = 1),
            0
        ) AS presencial_seats,
        COALESCE(
            SUM(offered_seats) FILTER (WHERE teaching_modality = 2),
            0
        ) AS ead_seats,
        COALESCE(
            SUM(entrants) FILTER (WHERE teaching_modality = 1),
            0
        ) AS presencial_entrants,
        COALESCE(
            SUM(entrants) FILTER (WHERE teaching_modality = 2),
            0
        ) AS ead_entrants
    FROM analytics.course_supply_snapshot
    WHERE cine_label_code IS NOT NULL
    GROUP BY census_year, institution_id, cine_label_code
)
SELECT
    *,
    CASE
        WHEN presencial_offers > 0 AND ead_offers > 0 THEN 'dual'
        WHEN presencial_offers > 0 THEN 'presencial'
        ELSE 'ead'
    END AS modality_state,
    ead_seats::NUMERIC
        / NULLIF(presencial_seats + ead_seats, 0) AS ead_seat_share,
    ead_entrants::NUMERIC
        / NULLIF(presencial_entrants + ead_entrants, 0) AS ead_entrant_share
FROM portfolio
WHERE FALSE;

TRUNCATE TABLE analytics.modality_portfolio_state_snapshot;

INSERT INTO analytics.modality_portfolio_state_snapshot
WITH portfolio AS (
    SELECT
        census_year,
        institution_id,
        cine_label_code,
        MAX(cine_label_name) AS cine_label_name,
        COUNT(*) FILTER (WHERE teaching_modality = 1)
            AS presencial_offers,
        COUNT(*) FILTER (WHERE teaching_modality = 2)
            AS ead_offers,
        COALESCE(
            SUM(offered_seats) FILTER (WHERE teaching_modality = 1),
            0
        ) AS presencial_seats,
        COALESCE(
            SUM(offered_seats) FILTER (WHERE teaching_modality = 2),
            0
        ) AS ead_seats,
        COALESCE(
            SUM(entrants) FILTER (WHERE teaching_modality = 1),
            0
        ) AS presencial_entrants,
        COALESCE(
            SUM(entrants) FILTER (WHERE teaching_modality = 2),
            0
        ) AS ead_entrants
    FROM analytics.course_supply_snapshot
    WHERE cine_label_code IS NOT NULL
    GROUP BY census_year, institution_id, cine_label_code
)
SELECT
    *,
    CASE
        WHEN presencial_offers > 0 AND ead_offers > 0 THEN 'dual'
        WHEN presencial_offers > 0 THEN 'presencial'
        ELSE 'ead'
    END AS modality_state,
    ead_seats::NUMERIC
        / NULLIF(presencial_seats + ead_seats, 0) AS ead_seat_share,
    ead_entrants::NUMERIC
        / NULLIF(presencial_entrants + ead_entrants, 0) AS ead_entrant_share
FROM portfolio;

CREATE INDEX IF NOT EXISTS modality_portfolio_state_key_idx
    ON analytics.modality_portfolio_state_snapshot (
        institution_id,
        cine_label_code,
        census_year
    );

CREATE INDEX IF NOT EXISTS modality_portfolio_state_year_idx
    ON analytics.modality_portfolio_state_snapshot (census_year);

ANALYZE analytics.modality_portfolio_state_snapshot;

CREATE OR REPLACE VIEW analytics.modality_portfolio_state AS
SELECT * FROM analytics.modality_portfolio_state_snapshot;

CREATE OR REPLACE VIEW analytics.modality_portfolio_transition AS
WITH bounds AS (
    SELECT MIN(census_year) AS first_year, MAX(census_year) AS last_year
    FROM analytics.course_supply_snapshot
),
paired AS (
    SELECT
        COALESCE(current_year.census_year, previous_year.census_year + 1)
            AS census_year,
        COALESCE(current_year.institution_id, previous_year.institution_id)
            AS institution_id,
        COALESCE(current_year.cine_label_code, previous_year.cine_label_code)
            AS cine_label_code,
        COALESCE(current_year.cine_label_name, previous_year.cine_label_name)
            AS cine_label_name,
        COALESCE(previous_year.modality_state, 'ausente')
            AS previous_state,
        COALESCE(current_year.modality_state, 'ausente')
            AS current_state,
        previous_year.presencial_seats AS previous_presencial_seats,
        current_year.presencial_seats AS current_presencial_seats,
        previous_year.ead_seats AS previous_ead_seats,
        current_year.ead_seats AS current_ead_seats,
        previous_year.ead_seat_share AS previous_ead_seat_share,
        current_year.ead_seat_share AS current_ead_seat_share
    FROM analytics.modality_portfolio_state AS current_year
    FULL OUTER JOIN analytics.modality_portfolio_state AS previous_year
        ON current_year.census_year = previous_year.census_year + 1
       AND current_year.institution_id = previous_year.institution_id
       AND current_year.cine_label_code = previous_year.cine_label_code
)
SELECT
    paired.*,
    previous_state || ' → ' || current_state AS transition,
    previous_state IS DISTINCT FROM current_state AS state_changed
FROM paired
CROSS JOIN bounds
WHERE paired.census_year BETWEEN bounds.first_year + 1 AND bounds.last_year;

-- Dependência agregada por área. As participações de vagas e ingressantes
-- separam expansão de capacidade e conversão efetiva.
CREATE OR REPLACE VIEW analytics.modality_dependency AS
SELECT
    census_year,
    cine_label_code,
    MAX(cine_label_name) AS cine_label_name,
    SUM(offered_seats) FILTER (WHERE teaching_modality = 1)
        AS presencial_seats,
    SUM(offered_seats) FILTER (WHERE teaching_modality = 2) AS ead_seats,
    SUM(entrants) FILTER (WHERE teaching_modality = 1)
        AS presencial_entrants,
    SUM(entrants) FILTER (WHERE teaching_modality = 2) AS ead_entrants,
    COALESCE(
        SUM(offered_seats) FILTER (WHERE teaching_modality = 2),
        0
    )::NUMERIC / NULLIF(SUM(offered_seats), 0) AS ead_seat_share,
    COALESCE(
        SUM(entrants) FILTER (WHERE teaching_modality = 2),
        0
    )::NUMERIC / NULLIF(SUM(entrants), 0) AS ead_entrant_share
FROM analytics.course_supply_snapshot
WHERE cine_label_code IS NOT NULL
GROUP BY census_year, cine_label_code;

-- Proxy de eficiência de conclusão para defasagens candidatas de 3, 4 e 5
-- anos. Ela compara concluintes no ano corrente aos ingressantes da mesma
-- oferta no ano-base. Não há identificação de indivíduos ou de coorte.
CREATE OR REPLACE VIEW analytics.lagged_completion_efficiency AS
SELECT
    current_year.census_year,
    current_year.institution_id,
    current_year.course_id,
    current_year.course_name,
    current_year.cine_label_code,
    current_year.teaching_modality,
    candidate.lag_years,
    base_year.census_year AS entrant_year,
    base_year.entrants AS lagged_entrants,
    current_year.graduates,
    base_year.entrants >= 20 AS is_eligible,
    current_year.graduates::NUMERIC
        / NULLIF(base_year.entrants, 0) AS lagged_completion_ratio,
    current_year.graduates > base_year.entrants AS exceeds_one
FROM analytics.course_supply_snapshot AS current_year
CROSS JOIN (VALUES (3), (4), (5)) AS candidate(lag_years)
JOIN analytics.course_supply_snapshot AS base_year
    ON base_year.institution_id = current_year.institution_id
   AND base_year.course_id = current_year.course_id
   AND base_year.teaching_modality = current_year.teaching_modality
   AND base_year.census_year = current_year.census_year - candidate.lag_years
WHERE current_year.graduates IS NOT NULL
  AND base_year.entrants IS NOT NULL;

CREATE OR REPLACE VIEW analytics.lagged_completion_summary AS
SELECT
    census_year,
    teaching_modality,
    lag_years,
    COUNT(*) AS eligible_offers,
    SUM(graduates) AS graduates,
    SUM(lagged_entrants) AS lagged_entrants,
    SUM(graduates)::NUMERIC
        / NULLIF(SUM(lagged_entrants), 0) AS aggregate_completion_ratio,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY lagged_completion_ratio
    ) AS median_offer_ratio,
    COUNT(*) FILTER (WHERE exceeds_one)::NUMERIC
        / COUNT(*) AS exceeds_one_share
FROM analytics.lagged_completion_efficiency
WHERE is_eligible
GROUP BY census_year, teaching_modality, lag_years;
