"""Geração do DDL raw a partir do perfil real das fontes."""

import json
import re
from pathlib import Path

IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _table_name(file_name: str) -> str:
    upper_name = file_name.upper()
    if "CURSOS" in upper_name:
        return "censo_superior_cursos_2024"
    if "IES" in upper_name:
        return "censo_superior_ies_2024"
    raise ValueError(f"Tabela não reconhecida: {file_name}")


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


def generate_raw_sql(profile_path: Path, output_directory: Path) -> list[Path]:
    """Gera tabelas raw e comandos psql de carga."""
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    output_directory.mkdir(parents=True, exist_ok=True)

    ddl_parts = [
        "-- Gerado a partir de reports/2024/source_profile.json.",
        "-- A camada raw preserva texto para impedir coerções silenciosas.",
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
            "data/interim/censo_superior_2024/" + table["file_name"]
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

    ddl_path = output_directory / "010_raw_2024.sql"
    copy_path = output_directory / "011_load_2024.psql"
    ddl_path.write_text("\n".join(ddl_parts), encoding="utf-8")
    copy_path.write_text("\n".join(copy_parts), encoding="utf-8")
    return [ddl_path, copy_path]
