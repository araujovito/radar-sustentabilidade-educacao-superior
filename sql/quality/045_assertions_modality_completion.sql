-- Diagnósticos das métricas de modalidade e conclusão defasada.

SELECT COUNT(*) AS invalid_modality_state_count
FROM analytics.modality_portfolio_state
WHERE modality_state NOT IN ('presencial', 'ead', 'dual');

SELECT COUNT(*) AS invalid_transition_year_count
FROM analytics.modality_portfolio_transition
WHERE census_year <= (
    SELECT MIN(census_year) FROM analytics.course_supply_snapshot
)
OR census_year > (
    SELECT MAX(census_year) FROM analytics.course_supply_snapshot
);

SELECT COUNT(*) AS invalid_dependency_share_count
FROM analytics.modality_dependency
WHERE ead_seat_share NOT BETWEEN 0 AND 1
   OR ead_entrant_share NOT BETWEEN 0 AND 1;

SELECT COUNT(*) AS invalid_lag_count
FROM analytics.lagged_completion_efficiency
WHERE census_year - entrant_year <> lag_years
   OR lag_years NOT IN (3, 4, 5);

SELECT COUNT(*) AS invalid_eligibility_count
FROM analytics.lagged_completion_efficiency
WHERE is_eligible IS DISTINCT FROM (lagged_entrants >= 20);
