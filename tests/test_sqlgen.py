import json
from pathlib import Path

from radar_sustentabilidade.sqlgen import generate_raw_sql


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
