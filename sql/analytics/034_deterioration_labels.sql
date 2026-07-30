CREATE SCHEMA IF NOT EXISTS analytics;

-- Evento de deterioração em horizonte de dois anos.
--
-- Definição: uma oferta observada no ano de referência t deteriora se, em
-- t+2, as matrículas caem abaixo de metade do nível de t, ou se a oferta
-- deixa de ser observada no Censo.
--
-- Por que matrículas e não ingressantes: ingressantes são um fluxo com
-- coeficiente de variação em torno de 0,55 na série (ver
-- persistence_findings.md). Uma queda de um ano em ingressantes é
-- frequentemente ruído. Matrículas são o estoque de alunos, bem menos
-- volátil, e uma queda de metade do estoque em dois anos é deterioração
-- difícil de atribuir a oscilação.
--
-- Por que dois anos e não um: dá tempo de o efeito aparecer no estoque, que
-- responde mais lentamente que o fluxo, e é o horizonte em que uma decisão
-- institucional ainda é possível.
--
-- O desaparecimento entra no evento porque, do ponto de vista de decisão, uma
-- oferta que sai do Censo deixou de operar. A ambiguidade é real e está
-- registrada: pode ser encerramento ou mudança cadastral de código de curso.
-- A marca `disappeared_from_census` permite medir o desempenho do modelo com
-- e sem esses casos.

CREATE OR REPLACE VIEW analytics.offer_deterioration_labels AS
WITH base AS (
    SELECT
        institution_id,
        course_id,
        teaching_modality,
        census_year AS reference_year,
        enrollments AS base_enrollments,
        entrants AS base_entrants,
        offered_seats AS base_offered_seats
    FROM analytics.course_supply_snapshot
),
-- O horizonte é comparado por aritmética de ano, não por LEAD: a série tem
-- lacunas, e LEAD devolveria a próxima linha observada, que pode estar a
-- vários anos de distância.
horizon AS (
    SELECT
        base.institution_id,
        base.course_id,
        base.teaching_modality,
        base.reference_year,
        base.base_enrollments,
        base.base_entrants,
        base.base_offered_seats,
        future.enrollments AS horizon_enrollments,
        future.census_year IS NULL AS disappeared_from_census
    FROM base
    LEFT JOIN analytics.course_supply_snapshot AS future
        ON future.institution_id = base.institution_id
       AND future.course_id = base.course_id
       AND future.teaching_modality = base.teaching_modality
       AND future.census_year = base.reference_year + 2
)
SELECT
    institution_id,
    course_id,
    teaching_modality,
    reference_year,
    base_enrollments,
    base_entrants,
    base_offered_seats,
    horizon_enrollments,
    disappeared_from_census,
    -- O rótulo só é determinável quando o horizonte cabe na série carregada.
    reference_year + 2 <= 2024 AS label_is_observable,
    CASE
        WHEN reference_year + 2 > 2024 THEN NULL
        WHEN disappeared_from_census THEN TRUE
        WHEN base_enrollments IS NULL OR base_enrollments = 0 THEN NULL
        ELSE horizon_enrollments::NUMERIC
             < 0.5 * base_enrollments::NUMERIC
    END AS deteriorated
FROM horizon;
