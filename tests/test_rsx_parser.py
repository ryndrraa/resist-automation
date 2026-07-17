from __future__ import annotations

from pathlib import Path

import pytest

from resist_automation.exceptions import InvalidRSXError, MissingRSXElementError
from resist_automation.rsx.parser import parse_rsx


def test_parse_rsx_reads_required_model_data(sample_rsx: Path) -> None:
    parsed = parse_rsx(sample_rsx)

    assert parsed.metadata.version == "4.0.0.2475"
    assert parsed.metadata.modeller == "Amanda novika"
    assert parsed.earthquake.pga == 0.5
    assert parsed.building.num_storeys == 2
    assert parsed.building.storey_height == 3.6
    assert parsed.building.roof_height == 1.44
    assert parsed.building.area == 30
    assert parsed.building.perimeter_length == 22
    assert parsed.structures["x"].depth_m == 0.1
    assert parsed.structures["x"].depth_cm == 10
    assert parsed.structures["y"].depth_cm == 10
    assert parsed.structures["x"].class_name == "SteelTensionConcentricBracedFrame"


def test_parse_rsx_rejects_broken_xml(tmp_path: Path) -> None:
    path = tmp_path / "broken.rsx"
    path.write_text("<RESIST><Building>", encoding="utf-8")
    with pytest.raises(InvalidRSXError, match="XML.*rusak"):
        parse_rsx(path)


def test_parse_rsx_reports_missing_earthquake(tmp_path: Path) -> None:
    path = tmp_path / "missing.rsx"
    path.write_text("<RESIST><Building /></RESIST>", encoding="utf-8")
    with pytest.raises(MissingRSXElementError, match="Earthquake"):
        parse_rsx(path)
