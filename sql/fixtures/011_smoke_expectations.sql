-- Verificações sobre o fixture sintético.
--
-- Cada consulta falha o script inteiro se o resultado divergir do esperado.
-- Isso transforma o CI de "o SQL compila" em "o SQL calcula certo".
--
-- Executar com: psql -v ON_ERROR_STOP=1

\set ON_ERROR_STOP on

DO $$
DECLARE
    actual NUMERIC;
BEGIN
    -- ------------------------------------------------------------------
    -- Reconciliação da EAD
    -- ------------------------------------------------------------------

    -- Capacidade vem da dimensão 3, em nível nacional: 5.000 vagas.
    SELECT offered_seats INTO actual
    FROM analytics.course_supply
    WHERE census_year = 2024 AND institution_id = 2 AND course_id = 300;
    IF actual IS DISTINCT FROM 5000 THEN
        RAISE EXCEPTION 'Vagas EAD: esperado 5000, obtido %', actual;
    END IF;

    -- Alunos vêm da dimensão 2, somando os municípios: 300 + 200 = 500.
    SELECT entrants INTO actual
    FROM analytics.course_supply
    WHERE census_year = 2024 AND institution_id = 2 AND course_id = 300;
    IF actual IS DISTINCT FROM 500 THEN
        RAISE EXCEPTION 'Ingressantes EAD: esperado 500, obtido %', actual;
    END IF;

    -- Matrículas: 900 + 600 = 1500.
    SELECT enrollments INTO actual
    FROM analytics.course_supply
    WHERE census_year = 2024 AND institution_id = 2 AND course_id = 300;
    IF actual IS DISTINCT FROM 1500 THEN
        RAISE EXCEPTION 'Matriculas EAD: esperado 1500, obtido %', actual;
    END IF;

    -- A oferta EAD aparece uma única vez, não uma por dimensão.
    SELECT COUNT(*) INTO actual
    FROM analytics.course_supply
    WHERE census_year = 2024 AND institution_id = 2 AND course_id = 300;
    IF actual IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION 'Dupla contagem na EAD: % linhas', actual;
    END IF;

    -- A dimensão 4 é oferta no exterior e não pode entrar em nenhuma linha.
    -- Os valores 999 do fixture apareceriam se ela vazasse.
    SELECT COUNT(*) INTO actual
    FROM analytics.course_supply
    WHERE offered_seats = 999 OR entrants = 999 OR enrollments = 999;
    IF actual <> 0 THEN
        RAISE EXCEPTION 'Dimensao 4 vazou para o mart: % linhas', actual;
    END IF;

    -- ------------------------------------------------------------------
    -- Normalização da grafia divergente de 2020
    -- ------------------------------------------------------------------

    SELECT COUNT(*) INTO actual
    FROM raw.censo_superior_cursos_todos
    WHERE nu_ano_censo = '2020' AND co_cine_rotulo IS NULL;
    IF actual <> 0 THEN
        RAISE EXCEPTION
            'CO_CINE_ROTULO2 nao foi normalizado em 2020: % nulos', actual;
    END IF;

    SELECT COUNT(DISTINCT co_cine_rotulo) INTO actual
    FROM raw.censo_superior_cursos_todos
    WHERE nu_ano_censo = '2020';
    IF actual <> 3 THEN
        RAISE EXCEPTION
            'Rotulos distintos em 2020: esperado 3, obtido %', actual;
    END IF;

    -- ------------------------------------------------------------------
    -- Rótulo de deterioração
    -- ------------------------------------------------------------------

    -- Curso 200: matrículas caem de 260 em 2020 para 120 em 2022, menos de
    -- metade. O rótulo de 2020 deve marcar deterioração.
    SELECT deteriorated::INT INTO actual
    FROM analytics.offer_deterioration_labels
    WHERE reference_year = 2020 AND institution_id = 1 AND course_id = 200;
    IF actual IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION 'Queda de matriculas nao rotulada: %', actual;
    END IF;

    -- Curso 400 desaparece em 2021: o rótulo de 2019 deve marcar deterioração
    -- por desaparecimento.
    SELECT disappeared_from_census::INT INTO actual
    FROM analytics.offer_deterioration_labels
    WHERE reference_year = 2019 AND institution_id = 1 AND course_id = 400;
    IF actual IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION 'Desaparecimento nao detectado: %', actual;
    END IF;

    -- Curso 100 mantém matrículas crescentes: não pode ser rotulado.
    SELECT deteriorated::INT INTO actual
    FROM analytics.offer_deterioration_labels
    WHERE reference_year = 2020 AND institution_id = 1 AND course_id = 100;
    IF actual IS DISTINCT FROM 0 THEN
        RAISE EXCEPTION 'Oferta saudavel rotulada como deteriorada: %', actual;
    END IF;

    -- Sem horizonte dentro da série, o rótulo não existe.
    SELECT COUNT(*) INTO actual
    FROM analytics.offer_deterioration_labels
    WHERE reference_year = 2024 AND deteriorated IS NOT NULL;
    IF actual <> 0 THEN
        RAISE EXCEPTION 'Rotulo criado sem horizonte observavel: %', actual;
    END IF;

    -- ------------------------------------------------------------------
    -- Atributos sem informação futura
    -- ------------------------------------------------------------------

    -- Em 2018 o curso 100 tem exatamente um ano observado, ainda que a série
    -- siga até 2024. Um valor maior indicaria janela olhando adiante.
    SELECT years_observed_to_date INTO actual
    FROM analytics.offer_features
    WHERE reference_year = 2018 AND institution_id = 1 AND course_id = 100;
    IF actual IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION
            'Historico de 2018 contaminado pelo futuro: % anos', actual;
    END IF;

    -- Em 2022 o mesmo curso acumula cinco anos: 2018 a 2022.
    SELECT years_observed_to_date INTO actual
    FROM analytics.offer_features
    WHERE reference_year = 2022 AND institution_id = 1 AND course_id = 100;
    IF actual IS DISTINCT FROM 5 THEN
        RAISE EXCEPTION 'Historico de 2022: esperado 5, obtido %', actual;
    END IF;

    -- A defasagem de um ano precisa vir de 2021, não de qualquer linha
    -- anterior. Em 2021 o curso 100 tem 95 ingressantes sobre 100 vagas.
    SELECT ROUND(occupancy_rate_lag1, 6) INTO actual
    FROM analytics.offer_features
    WHERE reference_year = 2022 AND institution_id = 1 AND course_id = 100;
    IF actual IS DISTINCT FROM ROUND(95.0 / 100.0, 6) THEN
        RAISE EXCEPTION 'Defasagem de ocupacao incorreta: %', actual;
    END IF;

    -- O curso 400 é ausente em 2021, então a defasagem de 2022 seria nula se
    -- alguém o consultasse. Verifica o caso oposto: em 2020 o curso 400 tem
    -- defasagem vinda de 2019, com 12 ingressantes sobre 150 vagas.
    SELECT ROUND(occupancy_rate_lag1, 6) INTO actual
    FROM analytics.offer_features
    WHERE reference_year = 2020 AND institution_id = 1 AND course_id = 400;
    IF actual IS DISTINCT FROM ROUND(12.0 / 150.0, 6) THEN
        RAISE EXCEPTION
            'Defasagem por aritmetica de ano incorreta: %', actual;
    END IF;

    -- O curso 400 não é observado em 2021, então não pode ter atributos lá.
    SELECT COUNT(*) INTO actual
    FROM analytics.offer_features
    WHERE reference_year = 2021 AND institution_id = 1 AND course_id = 400;
    IF actual <> 0 THEN
        RAISE EXCEPTION 'Atributos criados para oferta ausente: %', actual;
    END IF;

    -- ------------------------------------------------------------------
    -- Ociosidade não mensurável
    -- ------------------------------------------------------------------

    -- Nenhuma oferta sem capacidade declarada pode ser marcada como ociosa.
    SELECT COUNT(*) INTO actual
    FROM analytics.course_supply_panel
    WHERE is_low_occupancy AND NOT has_measurable_occupancy;
    IF actual <> 0 THEN
        RAISE EXCEPTION 'Ociosidade atribuida sem capacidade: %', actual;
    END IF;

    -- ------------------------------------------------------------------
    -- Transição de modalidade e conclusão defasada
    -- ------------------------------------------------------------------

    SELECT COUNT(*) INTO actual
    FROM analytics.modality_portfolio_transition
    WHERE census_year = 2024
      AND institution_id = 1
      AND cine_label_code = '0100'
      AND previous_state = 'presencial'
      AND current_state = 'dual';
    IF actual IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION 'Transicao presencial-dual nao detectada: %', actual;
    END IF;

    -- Em 2022, o curso 100 conclui 65 estudantes. Quatro anos antes havia
    -- 80 ingressantes: a proxy precisa resultar em 65/80 = 0,8125.
    SELECT ROUND(lagged_completion_ratio, 4) INTO actual
    FROM analytics.lagged_completion_efficiency
    WHERE census_year = 2022
      AND institution_id = 1
      AND course_id = 100
      AND teaching_modality = 1
      AND lag_years = 4;
    IF actual IS DISTINCT FROM 0.8125 THEN
        RAISE EXCEPTION 'Conclusao defasada incorreta: %', actual;
    END IF;

    RAISE NOTICE 'Todas as verificacoes do fixture passaram.';
END
$$;
