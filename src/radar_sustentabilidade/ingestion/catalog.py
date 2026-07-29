"""Leitura do catálogo de fontes."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class Source:
    """Fonte de dados pronta para aquisição."""

    source_id: str
    title: str
    publisher: str
    reference_year: int
    download_url: str
    file_format: str

    @property
    def file_name(self) -> str:
        """Obtém um nome de arquivo seguro a partir da URL."""
        file_name = Path(urlparse(self.download_url).path).name
        if not file_name:
            raise ValueError(f"URL sem nome de arquivo: {self.download_url}")
        return file_name


def load_catalog(path: Path) -> dict:
    """Carrega o catálogo TOML."""
    with path.open("rb") as catalog_file:
        return tomllib.load(catalog_file)


def load_source(path: Path, source_id: str) -> Source:
    """Localiza uma fonte ativa pelo identificador."""
    catalog = load_catalog(path)
    matching = [
        source
        for source in catalog["sources"]
        if source["id"] == source_id and source["status"] == "active"
    ]

    if not matching:
        raise KeyError(f"Fonte ativa não encontrada: {source_id}")
    if len(matching) > 1:
        raise ValueError(f"Identificador de fonte duplicado: {source_id}")

    source = matching[0]
    return Source(
        source_id=source["id"],
        title=source["title"],
        publisher=source["publisher"],
        reference_year=source["reference_year"],
        download_url=source["download_url"],
        file_format=source["format"],
    )
