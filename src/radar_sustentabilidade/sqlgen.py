"""Geração do DDL raw a partir do perfil real das fontes."""

import json
import re
from pathlib import Path

IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
YEAR_PATTERN = re.compile(r"(?P<year>19\d{2}|20\d{2})")


def table_year(file_name: str) -> int:
    """Extrai o ano de referência do nome do arquivo oficial."""
    matches = YEAR_PATTERN.findall(file_name)
    if not matches:
        raise ValueError(f"Ano não encontrado no nome: {file_name}")
    if len(set(matches)) > 1:
        raise ValueError(f"Ano ambíguo no nome: {file_name}")
    return int(matches[0])


def table_kind(file_name: str) -> str:
    """Classifica a tabela oficial como cursos ou IES."""
    upper_name = file_name.upper()
    if "CURSOS" in upper_name:
        return "cursos"
    if "IES" in upper_name:
        return "ies"
    raise ValueError(f"Tabela não reconhecida: {file_name}")


def _table_name(file_name: str) -> str:
    return f"censo_superior_{table_kind(file_name)}_{table_year(file_name)}"


def _validated_columns(columns: list[str]) -> list[str]:
    invalid = [
        column for column in columns if not IDENTIFIER_PATTERN.match(column)
    ]
    if invalid:
        raise ValueError(f"Identificadores inválidos: {invalid}")

    normalized = [column.lower() for column in columns]
    if len(normalized) != len(set(normalized)):
        raise ValueError("Colunas duplicadas após normalização")
    return normalized


def _profile_year(profile: dict) -> int:
    years = {table_year(table["file_name"]) for table in profile["tables"]}
    if len(years) != 1:
        raise ValueError(f"Perfil com anos divergentes: {sorted(years)}")
    return years.pop()


def generate_raw_sql(profile_path: Path, output_directory: Path) -> list[Path]:
    """Gera tabelas raw e comandos psql de carga para um ano."""
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    output_directory.mkdir(parents=True, exist_ok=True)
    year = _profile_year(profile)

    ddl_parts = [
        f"-- Gerado a partir de reports/{year}/source_profile.json.",
        "-- A camada raw preserva texto para impedir coerções silenciosas.",
        "-- Cada ano tem sua própria tabela: o leiaute oficial varia entre",
        "-- edições e a união acontece apenas em staging.",
        "CREATE SCHEMA IF NOT EXISTS raw;",
        "",
    ]
    copy_parts = [
        r"\set ON_ERROR_STOP on",
        "-- Execute com psql a partir da raiz do projeto.",
        "",
    ]

    for table in profile["tables"]:
        table_name = _table_name(table["file_name"])
        columns = _validated_columns(table["columns"])
        definitions = ",\n".join(
            f"    {column} TEXT" for column in columns
        )
        ddl_parts.extend(
            [
                f"CREATE TABLE IF NOT EXISTS raw.{table_name} (",
                definitions,
                ");",
                "",
            ]
        )

        relative_path = (
            f"data/interim/censo_superior_{year}/" + table["file_name"]
        )
        column_list = ", ".join(columns)
        copy_parts.extend(
            [
                (
                    f"\\copy raw.{table_name} ({column_list}) "
                    f"FROM '{relative_path}' "
                    "(FORMAT csv, HEADER true, DELIMITER ';', "
                    "ENCODING 'LATIN1', QUOTE '\"');"
                ),
                "",
            ]
        )

    ddl_path = output_directory / f"010_raw_{year}.sql"
    copy_path = output_directory / f"011_load_{year}.psql"
    ddl_path.write_text("\n".join(ddl_parts), encoding="utf-8")
    copy_path.write_text("\n".join(copy_parts), encoding="utf-8")
    return [ddl_path, copy_path]
