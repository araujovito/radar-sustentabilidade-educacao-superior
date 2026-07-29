import tomllib
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "config" / "sources.toml"


def load_catalog() -> dict:
    with CATALOG_PATH.open("rb") as catalog_file:
        return tomllib.load(catalog_file)


def test_initial_scope_is_2024() -> None:
    catalog = load_catalog()

    assert catalog["scope"]["initial_year"] == 2024
    assert catalog["historical_series"]["start_year"] == 2014
    assert catalog["historical_series"]["end_year"] == 2024


def test_source_ids_are_unique() -> None:
    catalog = load_catalog()
    source_ids = [source["id"] for source in catalog["sources"]]

    assert len(source_ids) == len(set(source_ids))


def test_primary_source_uses_official_domains() -> None:
    catalog = load_catalog()
    primary_source = catalog["sources"][0]

    assert urlparse(primary_source["landing_url"]).hostname == "www.gov.br"
    assert (
        urlparse(primary_source["download_url"]).hostname
        == "download.inep.gov.br"
    )
