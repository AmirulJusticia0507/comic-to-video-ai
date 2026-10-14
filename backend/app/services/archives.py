from __future__ import annotations

import os
import re
import shutil
import zipfile
from pathlib import Path, PurePosixPath

import rarfile

from app.services.storage import MAX_IMAGE_SIZE_BYTES

MAX_ARCHIVE_SIZE_BYTES = 200 * 1024 * 1024
MAX_ARCHIVE_IMAGES = 100
MAX_EXTRACTED_SIZE_BYTES = 500 * 1024 * 1024
IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
ARCHIVE_SUFFIXES = frozenset({".zip", ".rar", ".7z", ".cbz", ".cbr", ".tar", ".gz", ".tgz"})


class ArchiveImportError(ValueError):
    pass


def _natural_key(name: str) -> list[str | int]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]


def _safe_image_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    return not path.is_absolute() and ".." not in path.parts and path.suffix.lower() in IMAGE_TYPES


def _reject_nested_archives(names: list[str]) -> None:
    for name in names:
        suffix = PurePosixPath(name.replace("\\", "/")).suffix.lower()
        if suffix in ARCHIVE_SUFFIXES:
            raise ArchiveImportError("nested archives are not allowed")


def _validate_entries(entries: list[tuple[str, int]]) -> list[tuple[str, int]]:
    _reject_nested_archives([name for name, _ in entries])
    images = [(name, size) for name, size in entries if _safe_image_name(name)]
    images.sort(key=lambda item: _natural_key(item[0]))
    if not images:
        raise ArchiveImportError("archive contains no supported images")
    if len(images) > MAX_ARCHIVE_IMAGES:
        raise ArchiveImportError(f"archive contains more than {MAX_ARCHIVE_IMAGES} images")
    if any(size > MAX_IMAGE_SIZE_BYTES for _, size in images):
        raise ArchiveImportError("one or more images exceed the 20 MB limit")
    if sum(size for _, size in images) > MAX_EXTRACTED_SIZE_BYTES:
        raise ArchiveImportError("archive extracted size exceeds 500 MB")
    return images


def _verify_image_bytes(name: str, data: bytes) -> str:
    suffix = PurePosixPath(name.replace("\\", "/")).suffix.lower()
    expected = IMAGE_TYPES[suffix]
    if expected == "image/png":
        valid = data[:8] == b"\x89PNG\r\n\x1a\n"
    elif expected == "image/jpeg":
        valid = data[:3] == b"\xff\xd8\xff"
    else:
        valid = data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    if not valid:
        raise ArchiveImportError(f"file {name} is not a valid image")
    if len(data) > MAX_IMAGE_SIZE_BYTES:
        raise ArchiveImportError("one or more images exceed the 20 MB limit")
    return expected


def _configure_unrar() -> None:
    override = os.environ.get("UNRAR_TOOL", "").strip()
    if override:
        rarfile.UNRAR_TOOL = override
        return
    found = shutil.which("unrar")
    if found:
        rarfile.UNRAR_TOOL = found
        return
    candidates = [
        Path(r"C:\Program Files\WinRAR\UnRAR.exe"),
        Path(r"C:\Program Files (x86)\WinRAR\UnRAR.exe"),
        Path(r"C:\Program Files\WinRAR\WinRAR.exe"),
        Path("/usr/bin/unrar"),
        Path("/usr/local/bin/unrar"),
    ]
    for candidate in candidates:
        if candidate.exists():
            rarfile.UNRAR_TOOL = str(candidate)
            return


def _missing_tool_message(exc: Exception) -> bool:
    text = str(exc).lower()
    return "cannot find" in text or "no tool" in text or "no such file" in text or "unrar" in text


def read_archive_images(path: Path, suffix: str) -> list[tuple[str, bytes, str]]:
    suffix = suffix.lower()
    try:
        if suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                infos = [info for info in archive.infolist() if not info.is_dir()]
                for info in infos:
                    if info.flag_bits & 0x1:
                        raise ArchiveImportError("encrypted archives are not supported")
                entries = _validate_entries([(info.filename, info.file_size) for info in infos])
                result = []
                total = 0
                for name, _ in entries:
                    data = archive.read(name)
                    total += len(data)
                    if total > MAX_EXTRACTED_SIZE_BYTES:
                        raise ArchiveImportError("archive extracted size exceeds 500 MB")
                    content_type = _verify_image_bytes(name, data)
                    result.append((name, data, content_type))
                return result
        if suffix == ".rar":
            _configure_unrar()
            with rarfile.RarFile(path) as archive:
                infos = {info.filename: info for info in archive.infolist() if info.is_file()}
                entries = _validate_entries([(name, info.file_size) for name, info in infos.items()])
                result = []
                total = 0
                for name, _ in entries:
                    data = archive.read(infos[name])
                    total += len(data)
                    if total > MAX_EXTRACTED_SIZE_BYTES:
                        raise ArchiveImportError("archive extracted size exceeds 500 MB")
                    content_type = _verify_image_bytes(name, data)
                    result.append((name, data, content_type))
                return result
    except ArchiveImportError:
        raise
    except (zipfile.BadZipFile, rarfile.Error, OSError, RuntimeError, NotImplementedError) as exc:
        if isinstance(exc, rarfile.Error) and _missing_tool_message(exc):
            raise ArchiveImportError(
                "unrar binary not found; install unrar (production) or WinRAR (Windows) "
                "or set UNRAR_TOOL to its full path"
            ) from exc
        raise ArchiveImportError(f"cannot read archive: {exc}") from exc
    raise ArchiveImportError("only ZIP and RAR archives are supported")
