from __future__ import annotations

import csv
import json
from pathlib import Path

from ..models import Scenario


def _rows(scenarios: list[Scenario]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario in scenarios:
        rows.append(
            {
                "scenario_id": scenario.scenario_id,
                "source_path": str(scenario.source_path),
                "pga": scenario.pga,
                "structure_x": scenario.structure_x.structure_id,
                "depth_x_cm": scenario.structure_x.depth_cm,
                "structure_y": scenario.structure_y.structure_id,
                "depth_y_cm": scenario.structure_y.depth_cm,
                "target_sheet": scenario.target_sheet,
                "target_row": scenario.target_row,
                "drift_ultimate_x": scenario.result_x.drift_ultimate,
                "braced_ultimate_x": scenario.result_x.braced_ultimate,
                "drift_service_x": scenario.result_x.drift_service,
                "braced_service_x": scenario.result_x.braced_service,
                "drift_ultimate_y": scenario.result_y.drift_ultimate,
                "braced_ultimate_y": scenario.result_y.braced_ultimate,
                "drift_service_y": scenario.result_y.drift_service,
                "braced_service_y": scenario.result_y.braced_service,
                "status": scenario.status,
                "notes": scenario.notes,
            }
        )
    return rows


def export_recap(path: Path, scenarios: list[Scenario]) -> Path:
    path = Path(path).expanduser().resolve()
    if path.suffix.lower() not in {".csv", ".json"}:
        raise ValueError("Rekap harus disimpan sebagai .csv atau .json.")
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = _rows(scenarios)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            fieldnames = list(rows[0]) if rows else ["scenario_id"]
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return path
