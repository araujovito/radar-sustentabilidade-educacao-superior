-- Estas consultas devem retornar zero linhas ou zero contagens.

-- Chave do mart: uma linha por ano, IES, curso e modalidade.
SELECT
    census_year,
    institution_id,
    course_id,
    teaching_modality,
    COUNT(*) AS duplicate_count
FROM analytics.course_supply_2024
GROUP BY
    census_year,
    institution_id,
    course_id,
    teaching_modality
HAVING COUNT(*) > 1;

-- Modalidade deve ser coerente com as dimensões usadas no staging.
SELECT COUNT(*) AS invalid_modality_count
FROM analytics.course_supply_2024
WHERE teaching_modality NOT IN (1, 2)
   OR teaching_modality IS NULL;
