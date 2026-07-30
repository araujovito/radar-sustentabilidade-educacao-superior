"""Interface de linha de comando."""

import json
from pathlib import Path

import typer

from radar_sustentabilidade import __version__
from radar_sustentabilidade.analysis import write_mvp_summary
from radar_sustentabilidade.ingestion.archive import (
    extract_csv_members,
    write_inventory,
)
from radar_sustentabilidade.ingestion.catalog import load_source
from radar_sustentabilidade.ingestion.download import (
    download_source,
    import_local_source,
)
from radar_sustentabilidade.ingestion.profile import write_package_profile
from radar_sustentabilidade.longitudinal import (
    common_columns,
    generate_longitudinal_sql,
    load_profiles,
    year_only_columns,
)
from radar_sustentabilidade.quality import write_course_quality_profile
from radar_sustentabilidade.sqlgen import generate_raw_sql

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Comandos do Radar de Sustentabilidade."""


@app.command()
def version() -> None:
    """Exibe a versão instalada."""
    typer.echo(__version__)


@app.command()
def download(
    source_id: str,
    catalog: Path = Path("config/sources.toml"),
    data_dir: Path = Path("data/raw"),
) -> None:
    """Baixa uma fonte oficial e cria seu manifesto."""
    source = load_source(catalog, source_id)
    manifest = download_source(source, data_dir)
    typer.echo(json.dumps(manifest, ensure_ascii=False, indent=2))


@app.command()
def inventory(
    archive: Path,
    output: Path | None = None,
) -> None:
    """Valida um ZIP e registra seus membros sem extrair."""
    output_path = output or archive.with_name("archive_inventory.json")
    result = write_inventory(archive, output_path)
    typer.echo(
        f"{result['member_count']} membros inventariados em {output_path}"
    )


@app.command("import-file")
def import_file(
    source_id: str,
    input_path: Path,
    catalog: Path = Path("config/sources.toml"),
    data_dir: Path = Path("data/raw"),
) -> None:
    """Importa um arquivo obtido manualmente e cria seu manifesto."""
    source = load_source(catalog, source_id)
    manifest = import_local_source(source, input_path, data_dir)
    typer.echo(json.dumps(manifest, ensure_ascii=False, indent=2))


@app.command("profile-package")
def profile_package(
    archive: Path,
    output: Path = Path("reports/2024/source_profile.json"),
) -> None:
    """Perfila tabelas, hashes e dicionário de um pacote oficial."""
    result = write_package_profile(archive, output)
    typer.echo(
        f"{len(result['tables'])} tabelas perfiladas; relatório em {output}"
    )


@app.command("profile-quality")
def profile_quality(
    archive: Path,
    output: Path = Path("reports/2024/quality_profile.json"),
) -> None:
    """Perfila chaves, ausências e medidas da tabela de cursos."""
    result = write_course_quality_profile(archive, output)
    typer.echo(
        f"{result['row_count']} linhas perfiladas; relatório em {output}"
    )


@app.command("generate-sql")
def generate_sql(
    profile: Path = Path("reports/2024/source_profile.json"),
    output_dir: Path = Path("sql/generated"),
) -> None:
    """Gera o DDL raw e o script psql a partir do perfil real."""
    generated = generate_raw_sql(profile, output_dir)
    for path in generated:
        typer.echo(path)


@app.command("extract-tables")
def extract_tables(
    archive: Path,
    output_dir: Path = Path("data/interim/censo_superior_2024"),
) -> None:
    """Extrai somente os CSVs do pacote e registra seus hashes."""
    manifest = extract_csv_members(archive, output_dir)
    typer.echo(
        f"{manifest['extracted_file_count']} tabelas extraídas em {output_dir}"
    )


@app.command("generate-longitudinal-sql")
def generate_longitudinal(
    start_year: int = 2014,
    end_year: int = 2024,
    reports_dir: Path = Path("reports"),
    output_dir: Path = Path("sql/generated"),
) -> None:
    """Gera a união das camadas raw anuais pela interseção documentada."""
    years = list(range(start_year, end_year + 1))
    output_path = generate_longitudinal_sql(reports_dir, years, output_dir)
    typer.echo(output_path)


@app.command("report-layout-drift")
def report_layout_drift(
    start_year: int = 2014,
    end_year: int = 2024,
    reports_dir: Path = Path("reports"),
) -> None:
    """Compara os leiautes das edições e destaca as colunas instáveis."""
    years = list(range(start_year, end_year + 1))
    profiles = load_profiles(reports_dir, years)

    for kind in ("cursos", "ies"):
        shared = common_columns(profiles, kind)
        typer.echo(f"{kind}: {len(shared)} colunas comuns a {len(years)} anos")
        for year, columns in year_only_columns(profiles, kind).items():
            if columns:
                typer.echo(f"  somente em {year}: {', '.join(columns)}")


@app.command("build-mvp")
def build_mvp(
    courses_csv: Path = Path(
        "data/interim/censo_superior_2024/MICRODADOS_CADASTRO_CURSOS_2024.CSV"
    ),
    institutions_csv: Path = Path(
        "data/interim/censo_superior_2024/MICRODADOS_ED_SUP_IES_2024.CSV"
    ),
    output: Path = Path("reports/2024/mvp_summary.json"),
) -> None:
    """Constrói indicadores de oferta e concentração do recorte 2024."""
    summary = write_mvp_summary(courses_csv, output, institutions_csv)
    typer.echo(f"{summary['row_count']} ofertas analisadas; relatório em {output}")


if __name__ == "__main__":
    app()
