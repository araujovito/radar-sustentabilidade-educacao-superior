import json
from pathlib import Path

import pytest

from radar_sustentabilidade.sqlgen import generate_raw_sql, table_year


def test_generates_raw_ddl_and_psql_copy(tmp_path: Path) -> None:
    profile = {
        "tables": [
            {
                "file_name": "MICRODADOS_CADASTRO_CURSOS_2024.CSV",
                "columns": ["NU_ANO_CENSO", "CO_CURSO", "QT_MAT"],
            },
            {
                "file_name": "MICRODADOS_ED_SUP_IES_2024.CSV",
                "columns": ["NU_ANO_CENSO", "CO_IES", "NO_IES"],
            },
        ]
    }
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    ddl_path, copy_path = generate_raw_sql(
        profile_path,
        tmp_path / "sql",
    )
    ddl = ddl_path.read_text(encoding="utf-8")
    copy = copy_path.read_text(encoding="utf-8")

    assert "raw.censo_superior_cursos_2024" in ddl
    assert "co_curso TEXT" in ddl
    assert "raw.censo_superior_ies_2024" in ddl
    assert "ENCODING 'LATIN1'" in copy
    assert "DELIMITER ';'" in copy
    assert (
        "data/interim/censo_superior_2024/"
        "MICRODADOS_CADASTRO_CURSOS_2024.CSV"
    ) in copy
    assert ddl_path.name == "010_raw_2024.sql"
    assert copy_path.name == "011_load_2024.psql"


def test_generates_year_specific_tables_for_an_earlier_edition(
    tmp_path: Path,
) -> None:
    profile = {
        "tables": [
            {
                "file_name": "MICRODADOS_CADASTRO_CURSOS_2014.CSV",
                "columns": ["NU_ANO_CENSO", "CO_CURSO"],
            },
            {
                "file_name": "MICRODADOS_CADASTRO_IES_2014.CSV",
                "columns": ["NU_ANO_CENSO", "CO_IES"],
            },
        ]
    }
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    ddl_path, copy_path = generate_raw_sql(profile_path, tmp_path / "sql")

    assert ddl_path.name == "010_raw_2014.sql"
    assert copy_path.name == "011_load_2014.psql"
    assert "raw.censo_superior_cursos_2014" in ddl_path.read_text(
        encoding="utf-8"
    )
    assert (
        "data/interim/censo_superior_2014/"
        "MICRODADOS_CADASTRO_CURSOS_2014.CSV"
    ) in copy_path.read_text(encoding="utf-8")


def test_rejects_profile_mixing_reference_years(tmp_path: Path) -> None:
    profile = {
        "tables": [
            {
                "file_name": "MICRODADOS_CADASTRO_CURSOS_2023.CSV",
                "columns": ["CO_CURSO"],
            },
            {
                "file_name": "MICRODADOS_CADASTRO_IES_2024.CSV",
                "columns": ["CO_IES"],
            },
        ]
    }
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    with pytest.raises(ValueError, match="anos divergentes"):
        generate_raw_sql(profile_path, tmp_path / "sql")


def test_table_year_reads_the_reference_year_from_the_file_name() -> None:
    assert table_year("MICRODADOS_ED_SUP_IES_2022.CSV") == 2022

    with pytest.raises(ValueError, match="Ano não encontrado"):
        table_year("MICRODADOS_SEM_ANO.CSV")
