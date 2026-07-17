from __future__ import annotations

import json
import os
import sys
from pathlib import Path


SCHEMA_VERSION = 1
REQUIRED_SHEETS = ("Sheet1", "PGA 0,4", "PGA 0,5")
PGA_SHEETS = {0.4: "PGA 0,4", 0.5: "PGA 0,5"}
SCENARIO_ROWS = range(10, 19)
RESULT_FIELDS = (
    "drift_ultimate",
    "braced_ultimate",
    "drift_service",
    "braced_service",
)
RESULT_CELL_COLUMNS = {
    "x": {
        "drift_ultimate": "O",
        "braced_ultimate": "P",
        "drift_service": "S",
        "braced_service": "T",
    },
    "y": {
        "drift_ultimate": "W",
        "braced_ultimate": "X",
        "drift_service": "AA",
        "braced_service": "AB",
    },
}
SOURCE_ROOT = Path(__file__).resolve().parents[2]
IS_FROZEN = bool(getattr(sys, "frozen", False))
USER_DATA_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "RESIST Automation"
RUNTIME_DATA_ROOT = USER_DATA_ROOT if IS_FROZEN else SOURCE_ROOT / "data"
CONFIG_ROOT = USER_DATA_ROOT / "config" if IS_FROZEN else SOURCE_ROOT / "config"
DEFAULT_STRUCTURE_MAPPING = CONFIG_ROOT / "structure_mapping.json"


def ensure_runtime_directories() -> None:
    for path in (
        CONFIG_ROOT,
        RUNTIME_DATA_ROOT / "logs",
        RUNTIME_DATA_ROOT / "projects",
        RUNTIME_DATA_ROOT / "backups",
    ):
        path.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_STRUCTURE_MAPPING.exists():
        DEFAULT_STRUCTURE_MAPPING.write_text(
            json.dumps(
                {
                    "version": 1,
                    "mappings": [
                        {
                            "structure_id": "BFCTST",
                            "class": "SteelTensionConcentricBracedFrame",
                            "bracing_type": "Concentric Tension Only Bracing",
                        }
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
