from __future__ import annotations

import json
from pathlib import Path

from resist_automation.excel.reader import read_workbook_mapping
from resist_automation.models import ProjectSession
from resist_automation.project.serializer import load_session, save_session
from resist_automation.rsx.mapper import scenario_from_parsed
from resist_automation.rsx.parser import parse_rsx


def test_session_round_trip_uses_portable_paths(
    sample_rsx: Path,
    template_workbook: Path,
    tmp_path: Path,
) -> None:
    scenario = scenario_from_parsed(
        parse_rsx(sample_rsx),
        read_workbook_mapping(template_workbook),
    )
    session = ProjectSession(
        name="Uji Session",
        template_path=template_workbook,
        rsx_folder=sample_rsx.parent,
        scenarios=[scenario],
    )
    path = tmp_path / "project.json"
    save_session(session, path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert not Path(payload["template_path"]).is_absolute()
    restored = load_session(path)
    assert restored.name == session.name
    assert restored.template_path == template_workbook.resolve()
    assert restored.scenarios[0].source_path == sample_rsx.resolve()
    assert restored.scenarios[0].source_sha256 == scenario.source_sha256
