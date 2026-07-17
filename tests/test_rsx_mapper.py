from __future__ import annotations

from pathlib import Path

from resist_automation.excel.reader import read_workbook_mapping
from resist_automation.rsx.mapper import ids_from_filename, scenario_from_parsed, sheet_for_pga
from resist_automation.rsx.parser import parse_rsx


def test_filename_with_copy_suffix_is_parsed() -> None:
    assert ids_from_filename("0.5 BFCTST-BFCTST - Copy.rsx") == (0.5, "BFCTST", "BFCTST")


def test_supported_pga_sheet_tolerance() -> None:
    assert sheet_for_pga(0.40000001) == "PGA 0,4"
    assert sheet_for_pga(0.5) == "PGA 0,5"
    assert sheet_for_pga(0.6) is None


def test_bfctst_combination_maps_to_row_11(
    sample_rsx: Path,
    template_workbook: Path,
) -> None:
    scenario = scenario_from_parsed(
        parse_rsx(sample_rsx),
        read_workbook_mapping(template_workbook),
    )
    assert scenario.structure_x.structure_id == "BFCTST"
    assert scenario.structure_y.structure_id == "BFCTST"
    assert scenario.target_sheet == "PGA 0,5"
    assert scenario.target_row == 11
    assert scenario.status == "Siap diisi"
