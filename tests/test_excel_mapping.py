from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from resist_automation.excel.reader import read_workbook_mapping
from resist_automation.excel.validator import validate_workbook


def test_mapping_uses_code_cells_not_formula_cache(template_workbook: Path) -> None:
    mapping = read_workbook_mapping(template_workbook)
    entry = mapping.find(0.5, "BFCTST", "BFCTST")
    assert entry is not None
    assert entry.row == 11
    assert mapping.find(0.4, "BFCOST", "BFCTST").row == 13  # type: ignore[union-attr]


def test_template_formula_validation(template_workbook: Path) -> None:
    report = validate_workbook(template_workbook)
    assert report.valid

    workbook = load_workbook(template_workbook)
    workbook["Sheet1"]["D4"] = None
    workbook.save(template_workbook)
    workbook.close()
    report = validate_workbook(template_workbook)
    assert not report.valid
    assert any(issue.code == "MISSING_FORMULA" for issue in report.issues)
