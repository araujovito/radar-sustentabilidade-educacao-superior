import json
from pathlib import Path

import pytest

from radar_sustentabilidade.longitudinal import (
    build_union_sql,
    canonical_column,
    common_columns,
    generate_longitudinal_sql,
    year_only_columns,
)


def make_profile(year: int, course_columns: list, ies_columns: list) -> dict:
    return {
        "tables": [
            {
                "file_name": f"MICRODADOS_CADASTRO_CURSOS_{year}.CSV",
                "columns": course_columns,
            },
            {
                "file_name": f"MICRODADOS_CADASTRO_IES_{year}.CSV",
                "columns": ies_columns,
            },
        ]
    }


def test_normalizes_the_2020_cine_label_spelling() -> None:
    assert canonical_column("CO_CINE_ROTULO2") == "CO_CINE_ROTULO"
    assert canonical_column("co_cine_rotulo") == "CO_CINE_ROTULO"
    assert canonical_column("QT_MAT") == "QT_MAT"


def test_common_columns_exclude_columns_absent_in_any_year() -> None:
    profiles = {
        2020: make_profile(
            2020,
            ["NU_ANO_CENSO", "CO_CURSO", "CO_CINE_ROTULO2"],
            ["NU_ANO_CENSO", "CO_IES"],
        ),
        2021: make_profile(
            2021,
            ["NU_ANO_CENSO", "CO_CURSO", "CO_CINE_ROTULO"],
            ["NU_ANO_CENSO", "CO_IES", "CO_PROJETO"],
        ),
        2022: make_profile(
            2022,
            ["NU_ANO_CENSO", "CO_CURSO", "CO_CINE_ROTULO", "IN_COMUNITARIA"],
            ["NU_ANO_CENSO", "CO_IES"],
        ),
    }

    courses = common_columns(profiles, "cursos")

    assert courses == ["NU_ANO_CENSO", "CO_CURSO", "CO_CINE_ROTULO"]
    assert "IN_COMUNITARIA" not in courses
    assert common_columns(profiles, "ies") == ["NU_ANO_CENSO", "CO_IES"]


def test_year_only_columns_flag_single_edition_variables() -> None:
    profiles = {
        2020: make_profile(2020, ["CO_CURSO"], ["CO_IES"]),
        2021: make_profile(2021, ["CO_CURSO"], ["CO_IES", "CO_PROJETO"]),
        2022: make_profile(2022, ["CO_CURSO"], ["CO_IES"]),
    }

    assert year_only_columns(profiles, "ies")[2021] == ["CO_PROJETO"]
    assert year_only_columns(profiles, "ies")[2022] == []


def test_union_aliases_the_divergent_column_to_the_canonical_name() -> None:
    profiles = {
        2020: make_profile(
            2020, ["CO_CURSO", "CO_CINE_ROTULO2"], ["CO_IES"]
        ),
        2021: make_profile(
            2021, ["CO_CURSO", "CO_CINE_ROTULO"], ["CO_IES"]
        ),
    }

    sql = build_union_sql(profiles, "cursos")

    assert "co_cine_rotulo2 AS co_cine_rotulo" in sql
    assert "raw.censo_superior_cursos_2020" in sql
    assert "raw.censo_superior_cursos_2021" in sql
    assert "UNION ALL" in sql
    assert "co_cine_rotulo2 AS co_cine_rotulo2" not in sql


def test_generates_longitudinal_view_for_both_table_families(
    tmp_path: Path,
) -> None:
    reports = tmp_path / "reports"
    for year in (2023, 2024):
        directory = reports / str(year)
        directory.mkdir(parents=True)
        (directory / "source_profile.json").write_text(
            json.dumps(
                make_profile(
                    year,
                    ["NU_ANO_CENSO", "CO_CURSO", "QT_MAT"],
                    ["NU_ANO_CENSO", "CO_IES"],
                )
            ),
            encoding="utf-8",
        )

    output = generate_longitudinal_sql(reports, [2023, 2024], tmp_path / "sql")
    sql = output.read_text(encoding="utf-8")

    assert output.name == "012_raw_longitudinal.sql"
    assert "raw.censo_superior_cursos_todos" in sql
    assert "raw.censo_superior_ies_todos" in sql
    assert "2023 a 2024" in sql


def test_union_requires_at_least_two_years(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ao menos dois anos"):
        generate_longitudinal_sql(tmp_path, [2024], tmp_path / "sql")


def test_rejects_year_without_the_requested_table(tmp_path: Path) -> None:
    profiles = {
        2023: make_profile(2023, ["CO_CURSO"], ["CO_IES"]),
        2024: {
            "tables": [
                {
                    "file_name": "MICRODADOS_CADASTRO_CURSOS_2024.CSV",
                    "columns": ["CO_CURSO"],
                }
            ]
        },
    }

    with pytest.raises(ValueError, match="Anos sem tabela 'ies'"):
        common_columns(profiles, "ies")
