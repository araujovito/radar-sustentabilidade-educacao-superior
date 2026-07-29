"""Inventário seguro de arquivos ZIP."""

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
