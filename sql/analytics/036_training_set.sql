CREATE SCHEMA IF NOT EXISTS analytics;

-- Conjunto de treino e teste do sistema de alerta.
--
-- Separação fora do tempo, não aleatória: uma divisão aleatória colocaria a
-- mesma oferta em treino e teste em anos vizinhos, e o modelo aprenderia a
-- reconhecer a oferta em vez de antecipar deterioração.
--
-- Janela utilizável: o rótulo precisa de t+2 dentro da série (t <= 2022) e os
-- atributos precisam de dois anos de histórico para as variações (t >= 2016).
--
--   treino: 2016 a 2020
--   teste:  2021 a 2022
--
-- O intervalo entre o último ano de treino e o primeiro de teste não é
-- descartado, mas convém lembrar que o rótulo de 2020 usa 2022, o mesmo ano
-- de referência do teste. Isso não é vazamento de atributos — o modelo nunca
-- vê 2021 ou 2022 ao treinar — mas cria sobreposição de calendário entre o
-- horizonte de treino e o de teste, registrada aqui para leitura honesta das
-- métricas.
--
-- Escala mínima: ofertas com menos de 20 matrículas no ano de referência ficam
-- fora. Nelas, uma variação de poucos alunos cruza o limiar de metade do
-- estoque, e o rótulo mediria ruído em vez de deterioração.

CREATE OR REPLACE VIEW analytics.offer_training_set AS
SELECT
    features.institution_id,
    features.course_id,
    features.teaching_modality,
    features.reference_year,

    features.education_network,
    features.administrative_category,
    features.offered_seats,
    features.entrants,
    features.enrollments,
    features.occupancy_rate,
    features.has_measurable_occupancy,
    features.applications_per_seat,
    features.graduation_intensity,
    features.years_observed_to_date,
    features.measurable_years_to_date,
    features.low_occupancy_years_to_date,
    features.low_occupancy_share_to_date,
    features.current_low_occupancy_streak,
    features.mean_occupancy_to_date,
    features.demand_volatility_to_date,
    features.occupancy_rate_lag1,
    features.occupancy_change_1y,
    features.enrollment_growth_1y,
    features.seat_growth_1y,
    features.enrollment_growth_2y,
    features.institution_offer_count,
    features.institution_enrollment_hhi,

    labels.deteriorated,
    labels.disappeared_from_census,
    labels.base_enrollments,
    labels.horizon_enrollments,

    CASE
        WHEN features.reference_year BETWEEN 2016 AND 2020 THEN 'treino'
        WHEN features.reference_year BETWEEN 2021 AND 2022 THEN 'teste'
    END AS split
FROM analytics.offer_features AS features
JOIN analytics.offer_deterioration_labels AS labels
    ON labels.institution_id = features.institution_id
   AND labels.course_id = features.course_id
   AND labels.teaching_modality = features.teaching_modality
   AND labels.reference_year = features.reference_year
WHERE features.reference_year BETWEEN 2016 AND 2022
  AND labels.label_is_observable
  AND labels.deteriorated IS NOT NULL
  AND labels.base_enrollments >= 20;
