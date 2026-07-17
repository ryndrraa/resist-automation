from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..constants import DEFAULT_STRUCTURE_MAPPING, PGA_SHEETS
from ..models import ParsedRSX, Scenario, StructureAxis, WorkbookMapping
from ..utils.file_utils import sha256_file


FILENAME_PATTERN = re.compile(
    r"(?P<pga>0[\.,][45])\s+(?P<x>[A-Za-z0-9]+)\s*-\s*(?P<y>[A-Za-z0-9]+)",
    re.IGNORECASE,
)


def sheet_for_pga(pga: float) -> str | None:
    for supported, sheet in PGA_SHEETS.items():
        if abs(pga - supported) < 0.0001:
            return sheet
    return None


def ids_from_filename(filename: str) -> tuple[float, str, str] | None:
    match = FILENAME_PATTERN.search(Path(filename).stem)
    if not match:
        return None
    pga = float(match.group("pga").replace(",", "."))
    return pga, match.group("x").upper(), match.group("y").upper()


def load_structure_mapping(path: Path = DEFAULT_STRUCTURE_MAPPING) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Konfigurasi mapping struktur tidak dapat dibaca: {exc}") from exc
    mappings = payload.get("mappings", [])
    if not isinstance(mappings, list):
        raise ValueError("Konfigurasi structure_mapping.json harus memiliki array 'mappings'.")
    return [item for item in mappings if isinstance(item, dict)]


def _structure_id_from_config(
    structure: StructureAxis,
    mappings: list[dict[str, Any]],
) -> str | None:
    matches: list[str] = []
    for item in mappings:
        class_matches = item.get("class") == structure.class_name
        bracing_matches = item.get("bracing_type") == structure.bracing_type
        if class_matches and bracing_matches and item.get("structure_id"):
            matches.append(str(item["structure_id"]).upper())
    return matches[0] if len(set(matches)) == 1 else None


def scenario_from_parsed(
    parsed: ParsedRSX,
    workbook_mapping: WorkbookMapping,
    *,
    explicit_ids: tuple[str, str] | None = None,
    structure_mapping_path: Path = DEFAULT_STRUCTURE_MAPPING,
) -> Scenario:
    notes = list(parsed.warnings)
    file_mapping = ids_from_filename(parsed.source_path.name)
    mappings = load_structure_mapping(structure_mapping_path)

    if explicit_ids:
        structure_x_id, structure_y_id = (value.upper() for value in explicit_ids)
    elif file_mapping:
        filename_pga, structure_x_id, structure_y_id = file_mapping
        if abs(filename_pga - parsed.earthquake.pga) >= 0.0001:
            notes.append(
                f"PGA pada nama file ({filename_pga:g}) berbeda dari Earthquake.zone_factor "
                f"({parsed.earthquake.pga:g}); nilai XML digunakan."
            )
    else:
        structure_x_id = _structure_id_from_config(parsed.structures["x"], mappings)
        structure_y_id = _structure_id_from_config(parsed.structures["y"], mappings)

    parsed.structures["x"].structure_id = structure_x_id
    parsed.structures["y"].structure_id = structure_y_id

    target = None
    if structure_x_id and structure_y_id:
        target = workbook_mapping.find(parsed.earthquake.pga, structure_x_id, structure_y_id)
        if target is None:
            notes.append(
                f"Kombinasi {structure_x_id}-{structure_y_id} tidak tersedia pada template untuk "
                f"PGA {parsed.earthquake.pga:g}."
            )
    else:
        notes.append("ID struktur belum dapat dipastikan; pilih mapping secara manual.")

    stat = parsed.source_path.stat()
    scenario = Scenario(
        scenario_id=parsed.source_path.stem,
        source_path=parsed.source_path,
        pga=parsed.earthquake.pga,
        target_sheet=target.sheet if target else sheet_for_pga(parsed.earthquake.pga),
        target_row=target.row if target else None,
        structure_x=parsed.structures["x"],
        structure_y=parsed.structures["y"],
        notes="\n".join(notes),
        source_mtime_ns=stat.st_mtime_ns,
        source_sha256=sha256_file(parsed.source_path),
    )
    scenario.refresh_status()
    return scenario
