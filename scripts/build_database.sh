#!/usr/bin/env bash
# Aplica os scripts SQL do projeto na ordem correta de dependência.
#
# Uso:
#   scripts/build_database.sh              apenas esquemas e views
#   scripts/build_database.sh --fixture    também carrega o fixture sintético
#                                          e executa suas verificações
#
# Os scripts 011_load_*.psql são deliberadamente ignorados: eles copiam os
# CSVs oficiais do Inep, que não são versionados. A verificação automatizada
# usa o fixture sintético em sql/fixtures.
#
# Conexão pelas variáveis padrão do libpq: PGHOST, PGPORT, PGUSER, PGPASSWORD
# e PGDATABASE.

set -euo pipefail

FIRST_YEAR=2014
LAST_YEAR=2024
WITH_FIXTURE=0

if [ "${1:-}" = "--fixture" ]; then
    WITH_FIXTURE=1
fi

run() {
    echo "==> $1"
    psql --quiet --no-psqlrc -v ON_ERROR_STOP=1 -f "$1"
}

run sql/bootstrap/001_schemas.sql

for year in $(seq "$FIRST_YEAR" "$LAST_YEAR"); do
    run "sql/generated/010_raw_${year}.sql"
done

run sql/generated/012_raw_longitudinal.sql

run sql/staging/020_staging_2024.sql
run sql/staging/021_staging_longitudinal.sql

run sql/analytics/030_course_supply_2024.sql
run sql/analytics/035_institution_portfolio_2024.sql
run sql/analytics/031_course_supply_longitudinal.sql

if [ "$WITH_FIXTURE" -eq 1 ]; then
    # O fixture entra antes da materialização para que o snapshot e tudo o que
    # depende dele sejam construídos sobre dados reais, e não sobre vazio.
    run sql/fixtures/010_smoke_fixture.sql
fi

run sql/analytics/033_materialize_supply.sql
run sql/analytics/032_course_persistence.sql
run sql/analytics/034_deterioration_labels.sql
run sql/analytics/035_offer_features.sql
run sql/analytics/036_training_set.sql

if [ "$WITH_FIXTURE" -eq 1 ]; then
    # Reexecuta a materialização para provar que o script é idempotente com as
    # views dependentes já criadas. Uma versão anterior usava DROP TABLE e
    # falhava exatamente aqui.
    run sql/analytics/033_materialize_supply.sql

    run sql/fixtures/011_smoke_expectations.sql

    # Os arquivos de sql/quality são diagnósticos: imprimem contagens para
    # leitura humana sobre a base completa e não interrompem em divergência.
    # Aqui eles apenas confirmam que continuam sendo SQL válido contra o
    # esquema atual. O gate de comportamento é o arquivo de expectativas.
    for assertions in sql/quality/*.sql; do
        run "$assertions" > /dev/null
    done
fi

echo "Banco construído com sucesso."
