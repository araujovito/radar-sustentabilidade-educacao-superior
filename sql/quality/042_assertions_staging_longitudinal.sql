-- Asserções da camada staging longitudinal (2014-2024).
-- Estas consultas devem retornar zero linhas ou zero contagens.

-- A tipagem não pode perder chaves em nenhuma edição.
SELECT COUNT(*) AS unparsed_key_count
FROM staging.courses
WHERE census_year IS NULL
   OR institution_id IS NULL
   OR course_id IS NULL
   OR dimension_type IS NULL
   OR teaching_modality IS NULL
   OR academic_level IS NULL;

-- O ano tipado deve permanecer dentro do recorte.
SELECT COUNT(*) AS out_of_window_count
FROM staging.courses
WHERE census_year NOT BETWEEN 2014 AND 2024;

-- As onze edições devem estar presentes.
SELECT COUNT(*) AS missing_edition_count
FROM (
    SELECT generate_series(2014, 2024) AS expected_year
) AS expected
WHERE NOT EXISTS (
    SELECT 1
    FROM staging.courses
    WHERE census_year = expected.expected_year
);

-- A capacidade usada pelo mart vem das dimensões 1 e 3, que nunca deixam
-- QT_VG_TOTAL vazio. Um nulo aqui indicaria mudança de fonte ou de leiaute.
SELECT
    census_year,
    COUNT(*) AS null_capacity_count
FROM staging.courses
WHERE dimension_type IN (1, 3)
  AND offered_seats IS NULL
GROUP BY census_year;

-- Alunos vêm das dimensões 1 e 2, que nunca deixam QT_ING vazio.
SELECT
    census_year,
    COUNT(*) AS null_entrant_count
FROM staging.courses
WHERE dimension_type IN (1, 2)
  AND entrants IS NULL
GROUP BY census_year;

-- Rede de ensino deve existir em toda a série no arquivo de cursos.
SELECT COUNT(*) AS null_network_count
FROM staging.courses
WHERE education_network IS NULL;

-- A view de IES deve ter uma linha por ano e instituição.
SELECT COUNT(*) AS duplicate_institution_count
FROM (
    SELECT census_year, institution_id
    FROM staging.institutions
    GROUP BY census_year, institution_id
    HAVING COUNT(*) > 1
) AS duplicated;

-- Documenta a mudança de representação identificada em 2020: até 2019 as
-- medidas inaplicáveis a uma dimensão vinham vazias; a partir de 2020 vêm
-- como zero. A consulta falha se o padrão observado mudar, o que exigiria
-- revisar as métricas que usam média ou contagem.
SELECT COUNT(*) AS unexpected_blank_convention_count
FROM (
    SELECT
        census_year,
        COUNT(*) FILTER (
            WHERE dimension_type = 3 AND entrants IS NULL
        ) AS blank_rows,
        COUNT(*) FILTER (WHERE dimension_type = 3) AS dimension_rows
    FROM staging.courses
    GROUP BY census_year
) AS convention
WHERE (census_year <= 2019 AND blank_rows <> dimension_rows)
   OR (census_year >= 2020 AND blank_rows <> 0);
