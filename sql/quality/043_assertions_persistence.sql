-- Asserções do mart de persistência e volatilidade.
-- Estas consultas devem retornar zero linhas ou zero contagens.

-- A materialização deve reproduzir a view que a origina.
SELECT COUNT(*) AS snapshot_drift_count
FROM (
    SELECT census_year, institution_id, course_id, teaching_modality
    FROM analytics.course_supply
    EXCEPT
    SELECT census_year, institution_id, course_id, teaching_modality
    FROM analytics.course_supply_snapshot
) AS missing_in_snapshot;

SELECT COUNT(*) AS snapshot_surplus_count
FROM (
    SELECT census_year, institution_id, course_id, teaching_modality
    FROM analytics.course_supply_snapshot
    EXCEPT
    SELECT census_year, institution_id, course_id, teaching_modality
    FROM analytics.course_supply
) AS surplus_in_snapshot;

-- O mart longitudinal deve reproduzir o recorte de 2024 já validado.
SELECT COUNT(*) AS regression_against_2024_count
FROM (
    SELECT institution_id, course_id, teaching_modality, offered_seats,
           entrants, enrollments, graduates, applications
    FROM analytics.course_supply_snapshot
    WHERE census_year = 2024
    EXCEPT
    SELECT institution_id, course_id, teaching_modality, offered_seats,
           entrants, enrollments, graduates, applications
    FROM analytics.course_supply_2024
) AS divergent;

-- Contagens de anos não podem exceder os anos observados.
SELECT COUNT(*) AS impossible_count_rows
FROM analytics.course_persistence
WHERE low_occupancy_years > measurable_years
   OR current_low_occupancy_streak > low_occupancy_years
   OR current_low_occupancy_streak > measurable_years;

-- Proporções devem ficar no intervalo fechado de zero a um.
SELECT COUNT(*) AS out_of_range_share_count
FROM analytics.course_persistence
WHERE low_occupancy_share < 0
   OR low_occupancy_share > 1;

-- A janela observada não pode extrapolar o recorte carregado.
SELECT COUNT(*) AS out_of_window_count
FROM analytics.course_persistence
WHERE first_year < 2014
   OR last_year > 2024
   OR first_year > last_year;

-- Ofertas sem capacidade declarada não podem entrar como ociosas: seriam
-- ociosidade não mensurável, não ociosidade observada.
SELECT COUNT(*) AS unmeasurable_flagged_low_count
FROM analytics.course_supply_panel
WHERE is_low_occupancy
  AND NOT has_measurable_occupancy;

-- Volatilidade exige média positiva de ingressantes; o coeficiente de
-- variação nunca é negativo.
SELECT COUNT(*) AS negative_volatility_count
FROM analytics.course_persistence
WHERE demand_volatility < 0;
