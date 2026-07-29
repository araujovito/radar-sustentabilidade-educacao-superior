import hashlib
import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from urllib.request import Request
from zipfile import ZipFile

import pytest

from radar_sustentabilidade.ingestion.archive import (
    UnsafeArchiveError,
    inventory_zip,
)
from radar_sustentabilidade.ingestion.catalog import Source, load_source
from radar_sustentabilidade.ingestion.download import download_source


class FakeResponse(BytesIO):
    status = 200
    url = "https://download.inep.gov.br/example.zip"
    headers = {
        "ETag": '"example"',
        "Last-Modified": "Tue, 28 Jul 2026 00:00:00 GMT",
    }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class FakePartialResponse(FakeResponse):
    status = 206


def make_source() -> Source:
    return Source(
        source_id="example",
        title="Example",
        publisher="Inep",
        reference_year=2024,
        download_url="https://download.inep.gov.br/example.zip",
        file_format="zip",
    )


def test_loads_source_from_catalog() -> None:
    source = load_source(
        Path("config/sources.toml"),
        "inep_censo_superior_microdados_2024",
    )

    assert source.reference_year == 2024
    assert source.file_name.endswith(".zip")


def test_download_writes_file_and_manifest(tmp_path: Path) -> None:
    content = b"official data"
    captured_request: Request | None = None

    def opener(request: Request, timeout: int) -> FakeResponse:
        nonlocal captured_request
        captured_request = request
        assert timeout == 60
        return FakeResponse(content)

    retrieved_at = datetime(2026, 7, 28, tzinfo=UTC)
    manifest = download_source(
        make_source(),
        tmp_path,
        opener=opener,
        retrieved_at=retrieved_at,
    )

    target = tmp_path / "example" / "2024" / "example.zip"
    stored_manifest = json.loads(
        (target.parent / "manifest.json").read_text(encoding="utf-8")
    )

    assert target.read_bytes() == content
    assert manifest == stored_manifest
    assert manifest["sha256"] == hashlib.sha256(content).hexdigest()
    assert manifest["status"] == "downloaded"
    assert captured_request is not None
    assert captured_request.get_header("User-agent")


def test_existing_download_is_reused(tmp_path: Path) -> None:
    target = tmp_path / "example" / "2024" / "example.zip"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"already downloaded")

    def opener(*args, **kwargs):
        raise AssertionError("A rede não deveria ser acessada")

    manifest = download_source(make_source(), tmp_path, opener=opener)

    assert manifest["status"] == "reused"
    assert manifest["retrieved_at"] is None


def test_partial_download_is_resumed(tmp_path: Path) -> None:
    source = make_source()
    partial_path = (
        tmp_path
        / source.source_id
        / str(source.reference_year)
        / "example.zip.part"
    )
    partial_path.parent.mkdir(parents=True)
    partial_path.write_bytes(b"first-")

    def opener(request: Request, timeout: int) -> FakePartialResponse:
        assert request.get_header("Range") == "bytes=6-"
        return FakePartialResponse(b"second")

    manifest = download_source(source, tmp_path, opener=opener)
    final_path = partial_path.with_suffix("")

    assert final_path.read_bytes() == b"first-second"
    assert manifest["status"] == "downloaded"


def test_inventory_lists_members_without_extracting(tmp_path: Path) -> None:
    archive_path = tmp_path / "example.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("dados/example.csv", "a;b\n1;2\n")
        archive.writestr("documentacao/dicionario.xlsx", b"content")

    inventory = inventory_zip(archive_path)

    assert inventory["member_count"] == 2
    assert {member["path"] for member in inventory["members"]} == {
        "dados/example.csv",
        "documentacao/dicionario.xlsx",
    }
    assert not (tmp_path / "dados").exists()


def test_inventory_rejects_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.csv", "unsafe")

    with pytest.raises(UnsafeArchiveError, match="Caminho inseguro"):
        inventory_zip(archive_path)
