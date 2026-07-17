from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from resist_automation.excel.importer import import_results_from_workbook
from resist_automation.excel.reader import read_workbook_mapping
from resist_automation.rsx.mapper import scenario_from_parsed
from resist_automation.rsx.parser import parse_rsx


def test_import_previous_results_updates_mapped_scenario(
    sample_rsx: Path,
    template_workbook: Path,
) -> None:
    scenario = scenario_from_parsed(
        parse_rsx(sample_rsx),
        read_workbook_mapping(template_workbook),
    )
    workbook = load_workbook(template_workbook)
    worksheet = workbook["PGA 0,5"]
    for coordinate, value in {
        "O11": 38,
        "P11": 70,
        "S11": 46,
        "T11": 14,
        "W11": 37,
        "X11": 68,
        "AA11": 45,
        "AB11": 14,
    }.items():
        worksheet[coordinate] = value
    workbook.save(template_workbook)
    workbook.close()

    imported = import_results_from_workbook(template_workbook, [scenario])

    assert imported == 1
    assert scenario.result_x.drift_ultimate == 38
    assert scenario.result_y.braced_service == 14
    assert scenario.status == "Lengkap"
