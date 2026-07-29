"""Perfil de qualidade da tabela de cursos."""

import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

COURSE_COLUMNS = [
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

MEASURES = [
    "QT_CURSO",
    "QT_VG_TOTAL",
    "QT_INSCRITO_TOTAL",
    "QT_ING",
    "QT_MAT",
    "QT_CONC",
]

CANDIDATE_KEY = [
    "TP_DIMENSAO",
    "CO_IES",
    "CO_CURSO",
    "CO_MUNICIPIO",
    "TP_MODALIDADE_ENSINO",
]

DIMENSION_LABELS = {
    1: "presencial_brasil",
    2: "ead_alunos_por_localidade_brasil",
    3: "ead_oferta_nacional",
    4: "ead_instituicoes_brasileiras_exterior",
}


def _course_member(archive: ZipFile) -> str:
    matching = [
        name
        for name in archive.namelist()
        if "CURSOS" in Path(name).name.upper()
        and name.lower().endswith(".csv")
    ]
    if len(matching) != 1:
        raise ValueError(
            f"Esperado um CSV de cursos; encontrados {len(matching)}"
        )
    return matching[0]


def profile_course_quality(archive_path: Path) -> dict:
    """Calcula chaves, ausências e somas de controle por dimensão."""
    with ZipFile(archive_path) as archive:
        member_name = _course_member(archive)
        with archive.open(member_name) as stream:
            data = pd.read_csv(
                stream,
                sep=";",
                encoding="latin-1",
                usecols=COURSE_COLUMNS,
                low_memory=False,
            )

    dimension_summary = []
    for dimension, group in data.groupby("TP_DIMENSAO", dropna=False):
        dimension_value = None if pd.isna(dimension) else int(dimension)
        summary = {
            "dimension": dimension_value,
            "label": DIMENSION_LABELS.get(
                dimension_value,
                "categoria_desconhecida",
            ),
            "row_count": int(len(group)),
            "geography_complete_row_count": int(
                group[["CO_REGIAO", "CO_UF", "CO_MUNICIPIO"]]
                .notna()
                .all(axis=1)
                .sum()
            ),
            "distinct_ies_count": int(group["CO_IES"].nunique(dropna=True)),
            "distinct_course_count": int(
                group["CO_CURSO"].nunique(dropna=True)
            ),
            "modalities": sorted(
                int(value)
                for value in group["TP_MODALIDADE_ENSINO"].dropna().unique()
            ),
            "academic_levels": sorted(
                int(value)
                for value in group["TP_NIVEL_ACADEMICO"].dropna().unique()
            ),
            "measures": {},
        }
        for measure in MEASURES:
            summary["measures"][measure] = {
                "non_null_row_count": int(group[measure].notna().sum()),
                "non_zero_row_count": int(group[measure].ne(0).sum()),
                "sum": int(group[measure].sum()),
            }
        dimension_summary.append(summary)

    duplicated_key_rows = int(
        data.duplicated(CANDIDATE_KEY, keep=False).sum()
    )

    return {
        "schema_version": 1,
        "table_member": member_name,
        "row_count": int(len(data)),
        "column_subset": COURSE_COLUMNS,
        "candidate_key": CANDIDATE_KEY,
        "candidate_key_is_unique": duplicated_key_rows == 0,
        "rows_in_duplicated_candidate_key": duplicated_key_rows,
        "null_counts": {
            column: int(data[column].isna().sum())
            for column in COURSE_COLUMNS
        },
        "academic_level_counts": {
            str(int(level)): int(count)
            for level, count in data["TP_NIVEL_ACADEMICO"]
            .value_counts(dropna=False)
            .items()
            if not pd.isna(level)
        },
        "dimension_summary": dimension_summary,
    }


def write_course_quality_profile(
    archive_path: Path,
    output_path: Path,
) -> dict:
    """Gera e persiste o perfil de qualidade."""
    profile = profile_course_quality(archive_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return profile
