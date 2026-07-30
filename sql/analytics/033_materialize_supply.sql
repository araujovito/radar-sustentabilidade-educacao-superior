-- Materialização do mart de oferta longitudinal.
--
-- As views de analytics.course_supply reconstroem a união das onze tabelas
-- raw a cada consulta, o que torna o painel inviável para uso interativo.
-- Esta tabela materializa o resultado, com índices pelas chaves do painel, e
-- é reconstruída sempre que uma edição é recarregada.
--
-- É uma tabela, e não uma view materializada, para permitir os índices e o
-- ANALYZE explícito abaixo sem depender de recursos específicos de versão.
--
-- O script recarrega por TRUNCATE e INSERT, não por DROP e CREATE. Depois da
-- primeira execução existem views dependentes — course_supply_panel,
-- offer_features, offer_deterioration_labels e as que derivam delas — e um
-- DROP TABLE falharia. Só um DROP ... CASCADE passaria, e ele apagaria as
-- views em silêncio, deixando o banco incompleto sem aviso.

-- Cria a estrutura na primeira execução, sem carregar dados.
CREATE TABLE IF NOT EXISTS analytics.course_supply_snapshot AS
SELECT * FROM analytics.course_supply WHERE FALSE;

TRUNCATE TABLE analytics.course_supply_snapshot;

INSERT INTO analytics.course_supply_snapshot
SELECT * FROM analytics.course_supply;

CREATE INDEX IF NOT EXISTS course_supply_snapshot_offer_idx
    ON analytics.course_supply_snapshot (
        institution_id,
        course_id,
        teaching_modality,
        census_year
    );

CREATE INDEX IF NOT EXISTS course_supply_snapshot_year_idx
    ON analytics.course_supply_snapshot (census_year);

ANALYZE analytics.course_supply_snapshot;
