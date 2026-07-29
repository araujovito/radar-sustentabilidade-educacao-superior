"""Download idempotente e criação de manifesto."""

import hashlib
import json
import os
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO
from urllib.error import URLError
from urllib.request import Request, urlopen

from radar_sustentabilidade.ingestion.catalog import Source

CHUNK_SIZE = 1024 * 1024
USER_AGENT = "radar-sustentabilidade/0.1"


def sha256_file(path: Path) -> str:
    """Calcula SHA-256 sem carregar o arquivo inteiro na memória."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest(path: Path, manifest: dict) -> None:
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_path, path)


def _response_header(response: BinaryIO, name: str) -> str | None:
    headers = getattr(response, "headers", {})
    return headers.get(name) if headers else None


def download_source(
    source: Source,
    data_root: Path,
    *,
    opener: Callable = urlopen,
    retrieved_at: datetime | None = None,
    max_attempts: int = 4,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict:
    """Baixa uma fonte, calcula seu hash e persiste um manifesto atômico."""
    if max_attempts < 1:
        raise ValueError("max_attempts deve ser maior ou igual a 1")

    target_directory = data_root / source.source_id / str(source.reference_year)
    target_directory.mkdir(parents=True, exist_ok=True)

    final_path = target_directory / source.file_name
    partial_path = final_path.with_suffix(final_path.suffix + ".part")
    manifest_path = target_directory / "manifest.json"

    if final_path.exists():
        manifest = {
            "schema_version": 1,
            "source_id": source.source_id,
            "reference_year": source.reference_year,
            "source_url": source.download_url,
            "file_name": final_path.name,
            "file_size_bytes": final_path.stat().st_size,
            "sha256": sha256_file(final_path),
            "retrieved_at": None,
            "status": "reused",
        }
        _write_manifest(manifest_path, manifest)
        return manifest

    response_metadata = {}
    for attempt in range(1, max_attempts + 1):
        existing_bytes = (
            partial_path.stat().st_size if partial_path.exists() else 0
        )
        headers = {"User-Agent": USER_AGENT}
        if existing_bytes:
            headers["Range"] = f"bytes={existing_bytes}-"

        request = Request(source.download_url, headers=headers)
        try:
            with opener(request, timeout=60) as response:
                status = getattr(response, "status", 200)
                resume_download = bool(existing_bytes and status == 206)
                mode = "ab" if resume_download else "wb"

                with partial_path.open(mode) as output_file:
                    while chunk := response.read(CHUNK_SIZE):
                        output_file.write(chunk)

                response_metadata = {
                    "final_url": getattr(
                        response,
                        "url",
                        source.download_url,
                    ),
                    "etag": _response_header(response, "ETag"),
                    "last_modified": _response_header(
                        response,
                        "Last-Modified",
                    ),
                }
            break
        except (URLError, TimeoutError, ConnectionError, OSError):
            if attempt == max_attempts:
                raise
            sleeper(2 ** (attempt - 1))

    os.replace(partial_path, final_path)
    timestamp = retrieved_at or datetime.now(UTC)
    manifest = {
        "schema_version": 1,
        "source_id": source.source_id,
        "reference_year": source.reference_year,
        "source_url": source.download_url,
        "file_name": final_path.name,
        "file_size_bytes": final_path.stat().st_size,
        "sha256": sha256_file(final_path),
        "retrieved_at": timestamp.isoformat(),
        "status": "downloaded",
        **response_metadata,
    }
    _write_manifest(manifest_path, manifest)
    return manifest
