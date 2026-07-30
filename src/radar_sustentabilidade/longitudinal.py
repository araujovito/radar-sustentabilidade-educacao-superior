"""União longitudinal das camadas raw anuais.

As regras aplicadas aqui vêm de docs/layout_changes.md, que compara as onze
edições adquiridas. Nenhuma coluna entra na união sem existir em todos os anos
do recorte.
"""

import json
from pathlib import Path

from radar_sustentabilidade.sqlgen import table_kind, table_year

# Grafias divergentes que representam a mesma variável. O pacote de 2020
# publicou CO_CINE_ROTULO com um dígito extra; 2019 e 2021 usam o nome correto.
COLUMN_ALIASES = {"CO_CINE_ROTULO2": "CO_CINE_ROTULO"}


def canonical_column(column: str) -> str:
    """Resolve a grafia canônica de uma coluna."""
    upper = column.upper()
    return COLUMN_ALIASES.get(upper, upper)


def _columns_by_year(profiles: dict[int, dict], kind: str) -> dict[int, dict]:
    by_year: dict[int, dict] = {}
    for year, profile in profiles.items():
        for table in profile["tables"]:
            if table_kind(table["file_name"]) != kind:
                continue
            if table_year(table["file_name"]) != year:
                raise ValueError(
                    f"Perfil de {year} contém tabela de outro ano: "
                    f"{table['file_name']}"
                )
            by_year[year] = {
                canonical_column(column): column
                for column in table["columns"]
            }
    missing = sorted(set(profiles) - set(by_year))
    if missing:
        raise ValueError(f"Anos sem tabela '{kind}': {missing}")
    return by_year


def common_columns(profiles: dict[int, dict], kind: str) -> list[str]:
    """Lista as colunas presentes em todos os anos, em grafia canônica.

    A ordem segue o ano mais recente, que é o leiaute de referência do projeto.
    """
    by_year = _columns_by_year(profiles, kind)
    shared = set.intersection(*(set(columns) for columns in by_year.values()))
    latest = max(by_year)
    return [column for column in by_year[latest] if column in shared]


def year_only_columns(profiles: dict[int, dict], kind: str) -> dict[int, list]:
    """Mapeia colunas que existem em um único ano da série."""
    by_year = _columns_by_year(profiles, kind)
    counts: dict[str, int] = {}
    for columns in by_year.values():
        for column in columns:
            counts[column] = counts.get(column, 0) + 1
    return {
        year: sorted(column for column in columns if counts[column] == 1)
        for year, columns in sorted(by_year.items())
    }


def load_profiles(reports_directory: Path, years: list[int]) -> dict[int, dict]:
    """Carrega os perfis estruturais dos anos informados."""
    profiles = {}
    for year in years:
        path = reports_directory / str(year) / "source_profile.json"
        profiles[year] = json.loads(path.read_text(encoding="utf-8"))
    return profiles


def build_union_sql(profiles: dict[int, dict], kind: str) -> str:
    """Monta a view de união longitudinal para uma família de tabelas."""
    by_year = _columns_by_year(profiles, kind)
    columns = common_columns(profiles, kind)
    years = sorted(by_year)

    selects = []
    for year in years:
        available = by_year[year]
        projections = ",\n".join(
            f"        {available[column].lower()} AS {column.lower()}"
            for column in columns
        )
        selects.append(
            f"    SELECT\n{projections}\n"
            f"    FROM raw.censo_superior_{kind}_{year}"
        )

    body = "\n    UNION ALL\n".join(selects)
    return (
        f"CREATE OR REPLACE VIEW raw.censo_superior_{kind}_todos AS\n"
        f"{body}\n;"
    )


def generate_longitudinal_sql(
    reports_directory: Path,
    years: list[int],
    output_directory: Path,
) -> Path:
    """Gera a view que une as tabelas raw anuais pela interseção documentada."""
    if len(years) < 2:
        raise ValueError("A união longitudinal exige ao menos dois anos")

    profiles = load_profiles(reports_directory, years)
    output_directory.mkdir(parents=True, exist_ok=True)

    parts = [
        "-- Gerado a partir dos perfis estruturais de cada edição.",
        f"-- Recorte: {min(years)} a {max(years)}.",
        "-- Somente colunas presentes em todos os anos entram na união.",
        "-- Grafias divergentes são normalizadas; ver docs/layout_changes.md.",
        "",
    ]
    for kind in ("cursos", "ies"):
        shared = common_columns(profiles, kind)
        parts.extend(
            [
                f"-- {kind}: {len(shared)} colunas comuns aos "
                f"{len(years)} anos.",
                build_union_sql(profiles, kind),
                "",
            ]
        )

    output_path = output_directory / "012_raw_longitudinal.sql"
    output_path.write_text("\n".join(parts), encoding="utf-8")
    return output_path
