"""Inventário seguro de arquivos ZIP."""

import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZipInfo


class UnsafeArchiveError(ValueError):
    """Indica que o ZIP contém um membro inseguro."""


def _validate_member(member: ZipInfo) -> None:
    path = PurePosixPath(member.filename.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise UnsafeArchiveError(f"Caminho inseguro no ZIP: {member.filename}")

    unix_mode = member.external_attr >> 16
    if unix_mode and stat.S_ISLNK(unix_mode):
        raise UnsafeArchiveError(f"Link simbólico não permitido: {member.filename}")


def inventory_zip(archive_path: Path) -> dict:
    """Lista o conteúdo do ZIP sem extrair arquivos."""
    members = []
    total_uncompressed = 0
    total_compressed = 0

    with ZipFile(archive_path) as archive:
        for member in archive.infolist():
            _validate_member(member)
            total_uncompressed += member.file_size
            total_compressed += member.compress_size
            members.append(
                {
                    "path": member.filename,
                    "is_directory": member.is_dir(),
                    "compressed_size_bytes": member.compress_size,
                    "uncompressed_size_bytes": member.file_size,
                    "crc32": f"{member.CRC:08x}",
                }
            )

    return {
        "schema_version": 1,
        "archive_name": archive_path.name,
        "archive_size_bytes": archive_path.stat().st_size,
        "member_count": len(members),
        "total_compressed_size_bytes": total_compressed,
        "total_uncompressed_size_bytes": total_uncompressed,
        "members": members,
    }


def write_inventory(archive_path: Path, output_path: Path) -> dict:
    """Cria e persiste o inventário de um ZIP."""
    inventory = inventory_zip(archive_path)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_path, output_path)
    return inventory


def extract_csv_members(archive_path: Path, output_directory: Path) -> dict:
    """Extrai somente CSVs seguros e registra hashes SHA-256."""
    output_directory.mkdir(parents=True, exist_ok=True)
    extracted = []

    with ZipFile(archive_path) as archive:
        csv_members = [
            member
            for member in archive.infolist()
            if not member.is_dir()
            and member.filename.lower().endswith(".csv")
        ]
        for member in csv_members:
            _validate_member(member)
            output_path = output_directory / Path(member.filename).name
            if output_path.exists():
                raise FileExistsError(f"Destino já existe: {output_path}")

            temporary_path = output_path.with_suffix(
                output_path.suffix + ".part"
            )
            digest = hashlib.sha256()
            with archive.open(member) as source, temporary_path.open(
                "wb"
            ) as destination:
                while chunk := source.read(8 * 1024 * 1024):
                    destination.write(chunk)
                    digest.update(chunk)
            os.replace(temporary_path, output_path)
            extracted.append(
                {
                    "member_path": member.filename,
                    "file_name": output_path.name,
                    "file_size_bytes": output_path.stat().st_size,
                    "sha256": digest.hexdigest(),
                }
            )

    manifest = {
        "schema_version": 1,
        "archive_name": archive_path.name,
        "extracted_file_count": len(extracted),
        "files": extracted,
    }
    manifest_path = output_directory / "extraction_manifest.json"
    temporary_manifest = manifest_path.with_suffix(".json.tmp")
    temporary_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_manifest, manifest_path)
    return manifest
