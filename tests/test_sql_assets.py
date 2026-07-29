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
