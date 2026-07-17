from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..constants import SCHEMA_VERSION
from ..exceptions import SessionError, UnsupportedSessionVersionError
from ..models import ProjectSession
from ..services.backup_service import create_backup
from ..utils.file_utils import relative_path, resolve_stored_path


def _portable_payload(session: ProjectSession, base: Path) -> dict[str, Any]:
    payload = session.model_dump(mode="json")
    payload["template_path"] = relative_path(session.template_path, base)
    if session.rsx_folder is not None:
        payload["rsx_folder"] = relative_path(session.rsx_folder, base)
    for scenario_payload, scenario in zip(payload["scenarios"], session.scenarios, strict=True):
        scenario_payload["source_path"] = relative_path(scenario.source_path, base)
    payload["saved_at"] = datetime.now(timezone.utc).isoformat()
    return payload


def save_session(
    session: ProjectSession,
    path: Path,
    *,
    create_existing_backup: bool = True,
) -> Path:
    path = Path(path).expanduser().resolve()
    if path.suffix.lower() != ".json":
        raise SessionError("File proyek harus berekstensi .json.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and create_existing_backup:
        create_backup(path, path.parent / "backups")

    payload = _portable_payload(session, path.parent)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=".resist-session-",
        suffix=".json",
        dir=path.parent,
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        json.loads(temp_path.read_text(encoding="utf-8"))
        os.replace(temp_path, path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        temp_path.unlink(missing_ok=True)
        raise SessionError(f"Proyek tidak dapat disimpan: {exc}") from exc
    session.saved_at = datetime.now(timezone.utc)
    return path


def load_session(path: Path) -> ProjectSession:
    path = Path(path).expanduser().resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SessionError(f"File proyek tidak ditemukan: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SessionError(f"File proyek rusak atau tidak dapat dibaca: {exc}") from exc

    version = payload.get("schema_version")
    if version != SCHEMA_VERSION:
        raise UnsupportedSessionVersionError(
            f"Versi schema proyek {version!r} tidak didukung; versi aplikasi adalah {SCHEMA_VERSION}."
        )
    base = path.parent
    payload["template_path"] = resolve_stored_path(payload["template_path"], base)
    if payload.get("rsx_folder"):
        payload["rsx_folder"] = resolve_stored_path(payload["rsx_folder"], base)
    for scenario in payload.get("scenarios", []):
        scenario["source_path"] = resolve_stored_path(scenario["source_path"], base)
    try:
        return ProjectSession.model_validate(payload)
    except (ValidationError, KeyError, TypeError) as exc:
        raise SessionError(f"Isi file proyek tidak valid: {exc}") from exc
