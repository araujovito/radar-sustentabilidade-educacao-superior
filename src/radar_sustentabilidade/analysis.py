"""Construção do MVP analítico a partir dos CSVs oficiais."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

KEY_COLUMNS = ["NU_ANO_CENSO", "CO_IES", "CO_CURSO", "TP_MODALIDADE_ENSINO"]
LABEL_COLUMNS = ["NO_CURSO", "CO_CINE_ROTULO", "NO_CINE_ROTULO"]
NUMERIC_COLUMNS = [
    "QT_CURSO",
    "QT_VG_TOTAL",
    "QT_INSCRITO_TOTAL",
    "QT_ING",
    "QT_MAT",
    "QT_CONC",
]


def _aggregate_dimension(
    csv_path: Path,
    dimension: int,
    value_columns: list[str],
    chunksize: int,
) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    usecols = [
        *KEY_COLUMNS,
        "TP_DIMENSAO",
        "TP_NIVEL_ACADEMICO",
        *LABEL_COLUMNS,
        *value_columns,
    ]
    for chunk in pd.read_csv(
        csv_path,
        sep=";",
        encoding="latin1",
        usecols=list(dict.fromkeys(usecols)),
        chunksize=chunksize,
        low_memory=False,
    ):
        selected = chunk.loc[
            (chunk["TP_DIMENSAO"] == dimension)
            & (chunk["TP_NIVEL_ACADEMICO"] == 1)
        ].copy()
        if selected.empty:
            continue
        for column in value_columns:
            selected[column] = pd.to_numeric(selected[column], errors="coerce")
        aggregation = {column: "sum" for column in value_columns}
        aggregation.update({column: "first" for column in LABEL_COLUMNS})
        parts.append(selected.groupby(KEY_COLUMNS, as_index=False).agg(aggregation))

    if not parts:
        return pd.DataFrame(columns=[*KEY_COLUMNS, *LABEL_COLUMNS, *value_columns])
    combined = pd.concat(parts, ignore_index=True)
    aggregation = {column: "sum" for column in value_columns}
    aggregation.update({column: "first" for column in LABEL_COLUMNS})
    return combined.groupby(KEY_COLUMNS, as_index=False).agg(aggregation)


def build_course_mart(csv_path: Path, chunksize: int = 100_000) -> pd.DataFrame:
    """Reconcilia presencial e EAD na granularidade curso-IES-modalidade."""
    presencial = _aggregate_dimension(csv_path, 1, NUMERIC_COLUMNS, chunksize)
    ead_capacity = _aggregate_dimension(
        csv_path,
        3,
        ["QT_CURSO", "QT_VG_TOTAL", "QT_INSCRITO_TOTAL"],
        chunksize,
    )
    ead_students = _aggregate_dimension(
        csv_path, 2, ["QT_ING", "QT_MAT", "QT_CONC"], chunksize
    )
    ead = ead_capacity.merge(
        ead_students,
        on=KEY_COLUMNS,
        how="outer",
        suffixes=("", "_students"),
        validate="one_to_one",
        indicator=True,
    )
    for column in LABEL_COLUMNS:
        student_column = f"{column}_students"
        ead[column] = ead[column].fillna(ead[student_column])
        ead = ead.drop(columns=student_column)
    ead["missing_capacity_component"] = ead["_merge"].eq("right_only")
    ead["missing_student_component"] = ead["_merge"].eq("left_only")
    ead = ead.drop(columns="_merge")

    presencial["missing_capacity_component"] = False
    presencial["missing_student_component"] = False
    mart = pd.concat([presencial, ead], ignore_index=True)
    mart["seat_occupancy_rate"] = mart["QT_ING"] / mart["QT_VG_TOTAL"].replace(
        0, pd.NA
    )
    mart["applications_per_seat"] = (
        mart["QT_INSCRITO_TOTAL"] / mart["QT_VG_TOTAL"].replace(0, pd.NA)
    )
    mart["unconverted_seat_capacity"] = mart["QT_VG_TOTAL"] - mart["QT_ING"]
    mart["graduation_intensity"] = mart["QT_CONC"] / mart["QT_MAT"].replace(
        0, pd.NA
    )
    return mart


def _number(value: object) -> int | float | None:
    if pd.isna(value):
        return None
    number = float(value)
    return round(number, 6) if not number.is_integer() else int(number)


def summarize_mart(
    mart: pd.DataFrame,
    top_n: int = 10,
    institution_names: dict[int, str] | None = None,
) -> dict[str, object]:
    """Resume o mart sem publicar os microdados brutos."""
    institution_names = institution_names or {}
    by_modality: list[dict[str, object]] = []
    for modality, group in mart.groupby("TP_MODALIDADE_ENSINO"):
        seats = group["QT_VG_TOTAL"].sum()
        entrants = group["QT_ING"].sum()
        enrollments = group["QT_MAT"].sum()
        graduates = group["QT_CONC"].sum()
        by_modality.append(
            {
                "modality_code": int(modality),
                "course_offerings": int(group.shape[0]),
                "institutions": int(group["CO_IES"].nunique()),
                "offered_seats": _number(seats),
                "applications": _number(group["QT_INSCRITO_TOTAL"].sum()),
                "entrants": _number(entrants),
                "enrollments": _number(enrollments),
                "graduates": _number(graduates),
                "weighted_seat_occupancy_rate": _number(
                    entrants / seats if seats else None
                ),
                "graduation_intensity": _number(
                    graduates / enrollments if enrollments else None
                ),
            }
        )

    portfolio = mart.groupby(["CO_IES", "CO_CURSO"], as_index=False)["QT_MAT"].sum()
    portfolio["institution_enrollments"] = portfolio.groupby("CO_IES")[
        "QT_MAT"
    ].transform("sum")
    portfolio["share_squared"] = (
        portfolio["QT_MAT"] / portfolio["institution_enrollments"]
    ) ** 2
    concentration = (
        portfolio.loc[portfolio["institution_enrollments"] > 0]
        .groupby("CO_IES", as_index=False)
        .agg(
            enrollment_hhi=("share_squared", "sum"),
            course_count=("CO_CURSO", "nunique"),
            enrollments=("QT_MAT", "sum"),
        )
    )
    concentration = concentration.loc[
        (concentration["course_count"] >= 5)
        & (concentration["enrollments"] >= 1_000)
    ]
    concentration = concentration.nlargest(top_n, "enrollment_hhi")

    idle = mart.loc[
        (mart["QT_VG_TOTAL"] >= 100) & mart["seat_occupancy_rate"].notna()
    ].nlargest(top_n, "unconverted_seat_capacity")
    return {
        "method": {
            "unit": "ano + IES + curso + modalidade",
            "scope": "graduação, Brasil, 2024",
            "ead_reconciliation": (
                "capacidade da dimensão 3; alunos agregados da dimensão 2"
            ),
            "excluded_dimension": 4,
            "graduation_intensity_is_cohort_rate": False,
        },
        "row_count": int(mart.shape[0]),
        "unique_key": not bool(mart.duplicated(KEY_COLUMNS).any()),
        "missing_components": {
            "capacity": int(mart["missing_capacity_component"].sum()),
            "students": int(mart["missing_student_component"].sum()),
        },
        "by_modality": by_modality,
        "highest_unconverted_capacity": [
            {
                "institution_id": int(row.CO_IES),
                "institution_name": institution_names.get(int(row.CO_IES)),
                "course_id": int(row.CO_CURSO),
                "course_name": row.NO_CURSO,
                "modality_code": int(row.TP_MODALIDADE_ENSINO),
                "offered_seats": _number(row.QT_VG_TOTAL),
                "entrants": _number(row.QT_ING),
                "seat_occupancy_rate": _number(row.seat_occupancy_rate),
                "unconverted_seat_capacity": _number(
                    row.unconverted_seat_capacity
                ),
            }
            for row in idle.itertuples()
        ],
        "highest_portfolio_concentration": [
            {
                "institution_id": int(row.CO_IES),
                "institution_name": institution_names.get(int(row.CO_IES)),
                "enrollment_hhi": _number(row.enrollment_hhi),
                "course_count": int(row.course_count),
                "enrollments": _number(row.enrollments),
            }
            for row in concentration.itertuples()
        ],
    }


def write_mvp_summary(
    csv_path: Path,
    output_path: Path,
    institutions_csv: Path | None = None,
    chunksize: int = 100_000,
) -> dict[str, object]:
    """Constrói e grava o resumo versionável do MVP."""
    institution_names: dict[int, str] = {}
    if institutions_csv is not None:
        institutions = pd.read_csv(
            institutions_csv,
            sep=";",
            encoding="latin1",
            usecols=["CO_IES", "NO_IES"],
        )
        institution_names = dict(
            zip(
                institutions["CO_IES"].astype(int),
                institutions["NO_IES"],
                strict=True,
            )
        )
    summary = summarize_mart(
        build_course_mart(csv_path, chunksize=chunksize),
        institution_names=institution_names,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary
