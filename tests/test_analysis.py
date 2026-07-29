from pathlib import Path

import pandas as pd

from radar_sustentabilidade.analysis import build_course_mart, summarize_mart


def _write_courses(path: Path) -> None:
    rows = [
        [2024, 1, 10, 100, "Presencial", "01", "Área A", 1, 1, 1, 100, 150, 60, 80, 20],
        [2024, 2, 10, 200, "EAD", "02", "Área B", 2, 1, None, 0, 0, 70, 90, 15],
        [2024, 2, 10, 200, "EAD", "02", "Área B", 2, 1, None, 0, 0, 30, 40, 5],
        [2024, 3, 10, 200, "EAD", "02", "Área B", 2, 1, 1, 250, 300, 0, 0, 0],
        [2024, 4, 10, 300, "Exterior", "03", "Área C", 2, 1, 1, 10, 10, 5, 5, 1],
    ]
    columns = [
        "NU_ANO_CENSO", "TP_DIMENSAO", "CO_IES", "CO_CURSO", "NO_CURSO",
        "CO_CINE_ROTULO", "NO_CINE_ROTULO", "TP_MODALIDADE_ENSINO",
        "TP_NIVEL_ACADEMICO", "QT_CURSO", "QT_VG_TOTAL",
        "QT_INSCRITO_TOTAL", "QT_ING", "QT_MAT", "QT_CONC",
    ]
    pd.DataFrame(rows, columns=columns).to_csv(
        path, sep=";", encoding="latin1", index=False
    )


def test_build_course_mart_reconciles_ead_without_dimension_four(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "courses.csv"
    _write_courses(csv_path)
    mart = build_course_mart(csv_path, chunksize=2)

    assert len(mart) == 2
    ead = mart.loc[mart["TP_MODALIDADE_ENSINO"] == 2].iloc[0]
    assert ead["QT_VG_TOTAL"] == 250
    assert ead["QT_ING"] == 100
    assert ead["QT_MAT"] == 130
    assert ead["seat_occupancy_rate"] == 0.4


def test_summary_exposes_method_and_unique_key(tmp_path: Path) -> None:
    csv_path = tmp_path / "courses.csv"
    _write_courses(csv_path)
    summary = summarize_mart(build_course_mart(csv_path, chunksize=2))

    assert summary["unique_key"] is True
    assert summary["method"]["excluded_dimension"] == 4
    assert len(summary["by_modality"]) == 2
