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
