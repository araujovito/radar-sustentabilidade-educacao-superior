from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_generated_raw_schema_matches_profiled_column_count() -> None:
    ddl = (
        PROJECT_ROOT / "sql" / "generated" / "010_raw_2024.sql"
    ).read_text(encoding="utf-8")
    load_script = (
        PROJECT_ROOT / "sql" / "generated" / "011_load_2024.psql"
    ).read_text(encoding="utf-8")

    assert ddl.count(" TEXT") == 307
    assert load_script.count("\\copy ") == 2
    assert "ENCODING 'LATIN1'" in load_script


def test_every_edition_has_versioned_raw_assets() -> None:
    generated = PROJECT_ROOT / "sql" / "generated"

    for year in range(2014, 2025):
        ddl = generated / f"010_raw_{year}.sql"
        load_script = generated / f"011_load_{year}.psql"

        assert ddl.exists(), f"DDL ausente para {year}"
        assert load_script.exists(), f"Script de carga ausente para {year}"
        assert f"raw.censo_superior_cursos_{year}" in ddl.read_text(
            encoding="utf-8"
        )
        assert f"censo_superior_{year}/" in load_script.read_text(
            encoding="utf-8"
        )


def test_longitudinal_union_covers_the_documented_window() -> None:
    union = (
        PROJECT_ROOT / "sql" / "generated" / "012_raw_longitudinal.sql"
    ).read_text(encoding="utf-8")

    assert "raw.censo_superior_cursos_todos" in union
    assert "raw.censo_superior_ies_todos" in union
    # Onze edições geram dez uniões por família de tabela.
    assert union.count("UNION ALL") == 20
    # A grafia divergente de 2020 entra normalizada, não como coluna própria.
    assert "co_cine_rotulo2 AS co_cine_rotulo" in union
    assert "co_cine_rotulo2 AS co_cine_rotulo2" not in union
    # Colunas de uma única edição ficam fora da união.
    assert "qt_ing_rvppi" not in union
    assert "co_projeto" not in union


def test_longitudinal_assertions_check_grain_and_normalization() -> None:
    assertions = (
        PROJECT_ROOT
        / "sql"
        / "quality"
        / "041_assertions_longitudinal.sql"
    ).read_text(encoding="utf-8")

    assert "duplicate_key_count" in assertions
    assert "missing_cine_label_count" in assertions
    assert "invalid_dimension_count" in assertions


def test_longitudinal_staging_sources_network_from_the_course_file() -> None:
    staging = (
        PROJECT_ROOT
        / "sql"
        / "staging"
        / "021_staging_longitudinal.sql"
    ).read_text(encoding="utf-8")

    courses, institutions = staging.split(
        "CREATE OR REPLACE VIEW staging.institutions"
    )

    assert "raw.censo_superior_cursos_todos" in courses
    assert "raw.censo_superior_ies_todos" in institutions
    # TP_REDE só existe no arquivo de IES a partir de 2023, então a view
    # longitudinal de instituições não pode expô-la.
    assert "education_network" in courses
    assert "education_network" not in institutions
    # As views longitudinais não carregam sufixo de ano: o ano é uma coluna.
    assert "staging.courses_2024" not in staging


def test_staging_assertions_cover_typing_and_the_2020_convention() -> None:
    assertions = (
        PROJECT_ROOT
        / "sql"
        / "quality"
        / "042_assertions_staging_longitudinal.sql"
    ).read_text(encoding="utf-8")

    assert "unparsed_key_count" in assertions
    assert "missing_edition_count" in assertions
    assert "null_capacity_count" in assertions
    assert "unexpected_blank_convention_count" in assertions


def test_longitudinal_mart_keeps_the_validated_ead_reconciliation() -> None:
    analytics = (
        PROJECT_ROOT
        / "sql"
        / "analytics"
        / "031_course_supply_longitudinal.sql"
    ).read_text(encoding="utf-8")

    assert "staging.courses" in analytics
    assert "staging.courses_2024" not in analytics
    assert "dimension_type = 1" in analytics
    assert "dimension_type = 2" in analytics
    assert "dimension_type = 3" in analytics
    # A dimensão 4 é oferta no exterior e fica fora do recorte brasileiro.
    assert "dimension_type = 4" not in analytics
    assert "FULL OUTER JOIN ead_students" in analytics
    # A rede vem do arquivo de cursos, não da view de IES.
    assert "education_network" in analytics


def test_persistence_excludes_offers_without_declared_capacity() -> None:
    persistence = (
        PROJECT_ROOT / "sql" / "analytics" / "032_course_persistence.sql"
    ).read_text(encoding="utf-8")

    assert "has_measurable_occupancy" in persistence
    assert "WHERE has_measurable_occupancy" in persistence
    assert "current_low_occupancy_streak" in persistence
    assert "demand_volatility" in persistence
    # O painel lê a materialização, não a view que reconstrói a união.
    assert "FROM analytics.course_supply_snapshot" in persistence


def test_persistence_assertions_include_the_2024_regression() -> None:
    assertions = (
        PROJECT_ROOT / "sql" / "quality" / "043_assertions_persistence.sql"
    ).read_text(encoding="utf-8")

    assert "regression_against_2024_count" in assertions
    assert "snapshot_drift_count" in assertions
    assert "impossible_count_rows" in assertions
    assert "unmeasurable_flagged_low_count" in assertions


def test_features_never_read_the_retrospective_persistence_mart() -> None:
    features = (
        PROJECT_ROOT / "sql" / "analytics" / "035_offer_features.sql"
    ).read_text(encoding="utf-8")

    # Comentários citam o mart retrospectivo justamente para explicar por que
    # ele não entra. A verificação vale sobre o SQL efetivo.
    statements = "\n".join(
        line
        for line in features.splitlines()
        if not line.strip().startswith("--")
    )

    # course_persistence resume a série inteira, inclusive anos futuros a cada
    # observação. Lê-lo como atributo seria vazamento direto.
    assert "course_persistence" not in statements
    # Toda janela acumulada precisa terminar na linha corrente.
    assert "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW" in statements
    assert "UNBOUNDED FOLLOWING" not in statements
    assert "ROWS BETWEEN CURRENT ROW" not in statements
    # Defasagens por aritmética de ano, porque a série tem lacunas.
    assert "LAG(" not in statements.upper()
    assert "census_year - 1" in statements
    assert "census_year - 2" in statements


def test_labels_use_a_two_year_horizon_on_the_enrollment_stock() -> None:
    labels = (
        PROJECT_ROOT / "sql" / "analytics" / "034_deterioration_labels.sql"
    ).read_text(encoding="utf-8")

    assert "reference_year + 2" in labels
    assert "0.5 * base_enrollments" in labels
    assert "disappeared_from_census" in labels
    # O rótulo não pode existir quando o horizonte sai da série carregada.
    assert "label_is_observable" in labels
    # LEAD saltaria lacunas e compararia anos não adjacentes.
    assert "LEAD(" not in labels.upper()


def test_split_is_chronological_and_not_random() -> None:
    training = (
        PROJECT_ROOT / "sql" / "analytics" / "036_training_set.sql"
    ).read_text(encoding="utf-8")

    assert "BETWEEN 2016 AND 2020 THEN 'treino'" in training
    assert "BETWEEN 2021 AND 2022 THEN 'teste'" in training
    assert "RANDOM()" not in training.upper()
    # Escala mínima documentada para o rótulo não medir ruído.
    assert "base_enrollments >= 20" in training


def test_feature_assertions_prove_absence_of_leakage() -> None:
    assertions = (
        PROJECT_ROOT / "sql" / "quality" / "044_assertions_features.sql"
    ).read_text(encoding="utf-8")

    assert "temporal_leakage_count" in assertions
    # A prova recomputa sobre a série truncada em vez de inspecionar o SQL.
    assert "WHERE census_year <= 2019" in assertions
    assert "non_chronological_split_count" in assertions
    assert "label_beyond_series_count" in assertions


def test_materialization_reloads_without_dropping_dependent_views() -> None:
    script = (
        PROJECT_ROOT / "sql" / "analytics" / "033_materialize_supply.sql"
    ).read_text(encoding="utf-8")

    statements = "\n".join(
        line
        for line in script.splitlines()
        if not line.strip().startswith("--")
    )

    # DROP TABLE falha quando course_supply_panel, offer_features e as demais
    # views dependentes já existem; DROP ... CASCADE passaria, mas apagaria as
    # views em silêncio. A recarga precisa ser por TRUNCATE e INSERT.
    assert "DROP TABLE" not in statements
    assert "CASCADE" not in statements
    assert "TRUNCATE TABLE analytics.course_supply_snapshot" in statements
    assert "INSERT INTO analytics.course_supply_snapshot" in statements
    assert "CREATE TABLE IF NOT EXISTS" in statements
    assert "CREATE INDEX IF NOT EXISTS" in statements


def test_build_script_skips_the_official_load_scripts() -> None:
    script = (PROJECT_ROOT / "scripts" / "build_database.sh").read_text(
        encoding="utf-8"
    )

    # Os scripts de carga copiam CSVs do Inep, que não são versionados.
    assert "011_load_" not in script.replace(
        "# Os scripts 011_load_*.psql são deliberadamente ignorados", ""
    )
    # Aborta no primeiro erro, senão o CI passaria com o banco pela metade.
    assert "set -euo pipefail" in script
    assert "ON_ERROR_STOP=1" in script
    # A materialização roda duas vezes para provar idempotência.
    assert script.count("033_materialize_supply.sql") == 2


def test_modality_transition_uses_comparable_cine_portfolios() -> None:
    sql = (
        PROJECT_ROOT
        / "sql"
        / "analytics"
        / "037_modality_completion.sql"
    ).read_text(encoding="utf-8")

    assert "analytics.modality_portfolio_state" in sql
    assert "analytics.modality_portfolio_state_snapshot" in sql
    assert "TRUNCATE TABLE analytics.modality_portfolio_state_snapshot" in sql
    assert "CREATE INDEX IF NOT EXISTS modality_portfolio_state_key_idx" in sql
    assert "cine_label_code" in sql
    assert "previous_state || ' → ' || current_state" in sql
    assert "FULL OUTER JOIN analytics.modality_portfolio_state" in sql
    assert "ead_seat_share" in sql
    assert "ead_entrant_share" in sql


def test_lagged_completion_compares_exact_calendar_years() -> None:
    sql = (
        PROJECT_ROOT
        / "sql"
        / "analytics"
        / "037_modality_completion.sql"
    ).read_text(encoding="utf-8")

    assert "(VALUES (3), (4), (5))" in sql
    assert "current_year.census_year - candidate.lag_years" in sql
    assert "base_year.entrants >= 20 AS is_eligible" in sql
    assert "analytics.lagged_completion_summary" in sql
    assert "PERCENTILE_CONT(0.5)" in sql
    assert "LEAD(" not in sql.upper()
    assert "LAG(" not in sql.upper()


def test_modality_completion_assertions_cover_metric_bounds() -> None:
    assertions = (
        PROJECT_ROOT
        / "sql"
        / "quality"
        / "045_assertions_modality_completion.sql"
    ).read_text(encoding="utf-8")

    assert "invalid_modality_state_count" in assertions
    assert "invalid_dependency_share_count" in assertions
    assert "invalid_lag_count" in assertions
    assert "invalid_eligibility_count" in assertions


def test_workflow_runs_style_tests_and_the_sql_fixture() -> None:
    workflow = (
        PROJECT_ROOT / ".github" / "workflows" / "verificacao.yml"
    ).read_text(encoding="utf-8")

    assert "ruff check ." in workflow
    assert "pytest -q" in workflow
    assert "radar verify-portfolio" in workflow
    assert "postgres:17" in workflow
    assert "scripts/build_database.sh --fixture" in workflow
    # A versão mínima declarada em pyproject.toml precisa estar na matriz.
    assert '"3.11"' in workflow


def test_analytics_reconciles_ead_dimensions() -> None:
    analytics = (
        PROJECT_ROOT
        / "sql"
        / "analytics"
        / "030_course_supply_2024.sql"
    ).read_text(encoding="utf-8")

    assert "dimension_type = 1" in analytics
    assert "dimension_type = 2" in analytics
    assert "dimension_type = 3" in analytics
    assert "dimension_type = 4" not in analytics
    assert "FULL OUTER JOIN ead_students" in analytics
    assert "seat_occupancy_rate" in analytics


def test_portfolio_view_calculates_hhi_from_enrollment_shares() -> None:
    portfolio = (
        PROJECT_ROOT
        / "sql"
        / "analytics"
        / "035_institution_portfolio_2024.sql"
    ).read_text(encoding="utf-8")

    assert "POWER(" in portfolio
    assert "enrollment_hhi" in portfolio
    assert "PARTITION BY census_year, institution_id" in portfolio
