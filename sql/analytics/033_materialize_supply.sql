-- Materialização do mart de oferta longitudinal.
--
-- As views de analytics.course_supply reconstroem a união das onze tabelas
-- raw a cada consulta, o que torna o painel inviável para uso interativo.
-- Esta tabela materializa o resultado uma vez, com índices pelas chaves do
-- painel, e é reconstruída sempre que uma edição é recarregada.
--
-- É uma tabela, e não uma view materializada, para permitir os índices e o
-- ANALYZE explícito abaixo sem depender de recursos específicos de versão.

DROP TABLE IF EXISTS analytics.course_supply_snapshot;

CREATE TABLE analytics.course_supply_snapshot AS
SELECT * FROM analytics.course_supply;

CREATE INDEX course_supply_snapshot_offer_idx
    ON analytics.course_supply_snapshot (
        institution_id,
        course_id,
        teaching_modality,
        census_year
    );

CREATE INDEX course_supply_snapshot_year_idx
    ON analytics.course_supply_snapshot (census_year);

ANALYZE analytics.course_supply_snapshot;
