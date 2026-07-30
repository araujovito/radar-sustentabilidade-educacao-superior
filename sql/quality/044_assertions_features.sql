-- Asserções dos atributos e rótulos do sistema de alerta.
-- Estas consultas devem retornar zero linhas ou zero contagens.

-- ---------------------------------------------------------------------------
-- Prova de ausência de vazamento temporal.
--
-- A verificação não confia na leitura do SQL. Ela recomputa os atributos
-- acumulados usando apenas os anos até 2019 e compara com o que a view
-- produz para reference_year = 2019 tendo toda a série de 2014 a 2024
-- disponível. Se qualquer janela olhasse adiante, os valores divergiriam.
-- ---------------------------------------------------------------------------
WITH truncated AS (
    SELECT
        institution_id,
        course_id,
        teaching_modality,
        census_year,
        COALESCE(offered_seats > 0, FALSE) AS has_measurable_occupancy,
        COALESCE(
            offered_seats > 0 AND entrants::NUMERIC / offered_seats < 0.25,
            FALSE
        ) AS is_low_occupancy
    FROM analytics.course_supply_snapshot
    WHERE census_year <= 2019
),
recomputed AS (
    SELECT
        institution_id,
        course_id,
        teaching_modality,
        COUNT(*) AS years_observed,
        COUNT(*) FILTER (WHERE has_measurable_occupancy) AS measurable_years,
        COUNT(*) FILTER (WHERE is_low_occupancy) AS low_occupancy_years
    FROM truncated
    GROUP BY institution_id, course_id, teaching_modality
),
from_view AS (
    SELECT
        institution_id,
        course_id,
        teaching_modality,
        years_observed_to_date,
        measurable_years_to_date,
        low_occupancy_years_to_date
    FROM analytics.offer_features
    WHERE reference_year = 2019
)
SELECT COUNT(*) AS temporal_leakage_count
FROM from_view
JOIN recomputed USING (institution_id, course_id, teaching_modality)
WHERE from_view.years_observed_to_date <> recomputed.years_observed
   OR from_view.measurable_years_to_date <> recomputed.measurable_years
   OR from_view.low_occupancy_years_to_date <> recomputed.low_occupancy_years;

-- O acumulado nunca pode exceder o número de anos já decorridos no recorte.
SELECT COUNT(*) AS impossible_history_count
FROM analytics.offer_features
WHERE years_observed_to_date > reference_year - 2014 + 1
   OR measurable_years_to_date > years_observed_to_date
   OR low_occupancy_years_to_date > measurable_years_to_date
   OR current_low_occupancy_streak > measurable_years_to_date;

-- Concentração de portfólio é uma soma de quadrados de participações e deve
-- ficar no intervalo aberto de zero a um.
SELECT COUNT(*) AS out_of_range_hhi_count
FROM analytics.offer_features
WHERE institution_enrollment_hhi < 0
   OR institution_enrollment_hhi > 1.0000001;

-- ---------------------------------------------------------------------------
-- Rótulos
-- ---------------------------------------------------------------------------

-- O rótulo não pode ser determinável quando o horizonte sai da série.
SELECT COUNT(*) AS label_beyond_series_count
FROM analytics.offer_deterioration_labels
WHERE reference_year + 2 > 2024
  AND deteriorated IS NOT NULL;

-- Desaparecer do Censo implica deterioração pela definição adotada.
SELECT COUNT(*) AS inconsistent_disappearance_count
FROM analytics.offer_deterioration_labels
WHERE label_is_observable
  AND disappeared_from_census
  AND deteriorated IS NOT TRUE;

-- Uma oferta que permaneceu e manteve o estoque não pode estar marcada.
SELECT COUNT(*) AS false_positive_label_count
FROM analytics.offer_deterioration_labels
WHERE label_is_observable
  AND NOT disappeared_from_census
  AND base_enrollments > 0
  AND horizon_enrollments >= base_enrollments
  AND deteriorated;

-- ---------------------------------------------------------------------------
-- Conjunto de treino
-- ---------------------------------------------------------------------------

-- Treino e teste não podem compartilhar anos de referência.
SELECT COUNT(*) AS overlapping_split_count
FROM (
    SELECT reference_year
    FROM analytics.offer_training_set
    WHERE split = 'treino'
    INTERSECT
    SELECT reference_year
    FROM analytics.offer_training_set
    WHERE split = 'teste'
) AS overlap;

-- Todo ano de teste precisa ser posterior a todo ano de treino.
SELECT COUNT(*) AS non_chronological_split_count
FROM analytics.offer_training_set
WHERE split = 'teste'
  AND reference_year <= (
      SELECT MAX(reference_year)
      FROM analytics.offer_training_set
      WHERE split = 'treino'
  );

-- O conjunto de treino só admite linhas com rótulo determinado.
SELECT COUNT(*) AS undetermined_label_count
FROM analytics.offer_training_set
WHERE deteriorated IS NULL;
