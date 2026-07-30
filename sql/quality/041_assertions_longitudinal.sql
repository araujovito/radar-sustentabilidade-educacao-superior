-- Asserções da camada raw longitudinal (2014-2024).
-- Estas consultas devem retornar zero linhas ou zero contagens.

-- O grão oficial do arquivo de cursos deve ser único em todos os anos.
SELECT
    nu_ano_censo,
    COUNT(*) AS duplicate_key_count
FROM (
    SELECT
        nu_ano_censo,
        tp_dimensao,
        co_ies,
        co_curso,
        co_municipio,
        tp_modalidade_ensino,
        COUNT(*) AS row_count
    FROM raw.censo_superior_cursos_todos
    GROUP BY
        nu_ano_censo,
        tp_dimensao,
        co_ies,
        co_curso,
        co_municipio,
        tp_modalidade_ensino
    HAVING COUNT(*) > 1
) AS duplicated
GROUP BY nu_ano_censo;

-- Cada edição deve aparecer exatamente uma vez na união.
SELECT COUNT(*) AS unexpected_year_count
FROM (
    SELECT nu_ano_censo
    FROM raw.censo_superior_cursos_todos
    GROUP BY nu_ano_censo
) AS years
WHERE nu_ano_censo::int NOT BETWEEN 2014 AND 2024;

-- O ano declarado na coluna deve coincidir com a tabela de origem.
-- Um valor nulo indicaria falha de projeção na união.
SELECT COUNT(*) AS null_year_count
FROM raw.censo_superior_cursos_todos
WHERE nu_ano_censo IS NULL;

-- A normalização de CO_CINE_ROTULO2 deve deixar 2020 preenchido.
SELECT COUNT(*) AS missing_cine_label_count
FROM raw.censo_superior_cursos_todos
WHERE nu_ano_censo = '2020'
  AND co_cine_rotulo IS NULL;

-- As dimensões devem permanecer no domínio documentado.
SELECT COUNT(*) AS invalid_dimension_count
FROM raw.censo_superior_cursos_todos
WHERE tp_dimensao NOT IN ('1', '2', '3', '4')
   OR tp_dimensao IS NULL;

-- A tabela de IES deve ter uma linha por ano e instituição.
SELECT
    nu_ano_censo,
    COUNT(*) AS duplicate_institution_count
FROM (
    SELECT nu_ano_censo, co_ies, COUNT(*) AS row_count
    FROM raw.censo_superior_ies_todos
    GROUP BY nu_ano_censo, co_ies
    HAVING COUNT(*) > 1
) AS duplicated
GROUP BY nu_ano_censo;
