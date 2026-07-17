from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def create_backup(path: Path, backup_directory: Path | None = None) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"File yang akan dicadangkan tidak ditemukan: {path}")
    destination_dir = backup_directory or path.parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = destination_dir / f"{path.stem}.backup-{timestamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    return backup_path
