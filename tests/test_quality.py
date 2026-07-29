from pathlib import Path
from zipfile import ZipFile

from radar_sustentabilidade.quality import profile_course_quality

HEADER = [
    "NU_ANO_CENSO",
    "TP_DIMENSAO",
    "CO_REGIAO",
    "CO_UF",
    "CO_MUNICIPIO",
    "CO_IES",
    "CO_CURSO",
    "TP_MODALIDADE_ENSINO",
    "TP_NIVEL_ACADEMICO",
    "TP_GRAU_ACADEMICO",
    "QT_CURSO",
    "QT_VG_TOTAL",
    "QT_INSCRITO_TOTAL",
    "QT_ING",
    "QT_MAT",
    "QT_CONC",
]


def test_profiles_dimensions_and_candidate_key(tmp_path: Path) -> None:
    rows = [
        [2024, 1, 1, 11, 1101, 10, 100, 1, 1, 1, 1, 20, 40, 10, 30, 5],
        [2024, 2, 1, 11, 1101, 10, 200, 2, 1, 1, 0, 0, 0, 8, 20, 3],
        [2024, 3, "", "", "", 10, 200, 2, 1, 1, 1, 100, 50, 0, 0, 0],
    ]
    content = ";".join(HEADER) + "\n"
    content += "\n".join(";".join(map(str, row)) for row in rows) + "\n"

    archive_path = tmp_path / "package.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "dados/MICRODADOS_CADASTRO_CURSOS_2024.CSV",
            content.encode("latin-1"),
        )

    profile = profile_course_quality(archive_path)
    dimensions = {
        item["dimension"]: item for item in profile["dimension_summary"]
    }

    assert profile["row_count"] == 3
    assert profile["candidate_key_is_unique"] is True
    assert dimensions[1]["measures"]["QT_VG_TOTAL"]["sum"] == 20
    assert dimensions[2]["measures"]["QT_ING"]["sum"] == 8
    assert dimensions[3]["geography_complete_row_count"] == 0
