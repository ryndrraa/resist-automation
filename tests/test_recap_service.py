from __future__ import annotations

import json
from pathlib import Path

from resist_automation.excel.reader import read_workbook_mapping
from resist_automation.rsx.mapper import scenario_from_parsed
from resist_automation.rsx.parser import parse_rsx
from resist_automation.services.recap_service import export_recap


def test_recap_exports_csv_and_json(
    sample_rsx: Path,
    template_workbook: Path,
    tmp_path: Path,
) -> None:
    scenario = scenario_from_parsed(
        parse_rsx(sample_rsx),
        read_workbook_mapping(template_workbook),
    )
    csv_path = export_recap(tmp_path / "rekap.csv", [scenario])
    json_path = export_recap(tmp_path / "rekap.json", [scenario])

    assert "scenario_id" in csv_path.read_text(encoding="utf-8-sig")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload[0]["target_row"] == 11
    assert payload[0]["structure_x"] == "BFCTST"
