from __future__ import annotations

import hashlib
import os
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(path: Path, base: Path) -> str:
    resolved_path = path.expanduser().resolve()
    resolved_base = base.expanduser().resolve()
    try:
        return os.path.relpath(resolved_path, resolved_base)
    except ValueError:
        return str(resolved_path)


def resolve_stored_path(value: str, base: Path) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (base / candidate).resolve()
