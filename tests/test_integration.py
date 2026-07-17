from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from resist_automation.excel.reader import read_workbook_mapping
from resist_automation.excel.writer import export_project_to_excel
from resist_automation.models import AxisResult
from resist_automation.rsx.mapper import scenario_from_parsed
from resist_automation.rsx.parser import parse_rsx
from resist_automation.utils.file_utils import sha256_file


def test_acceptance_flow_with_supplied_workbook(sample_rsx: Path, tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    template = root / "Lembar Kerja Software RESIST - Unit Eficiency.xlsx"
    assert template.exists(), "Workbook yang diberikan pengguna harus tersedia untuk integration test."
    original_hash = sha256_file(template)
    scenario = scenario_from_parsed(parse_rsx(sample_rsx), read_workbook_mapping(template))
    scenario.result_x = AxisResult(
        drift_ultimate=38,
        braced_ultimate=70,
        drift_service=46,
        braced_service=14,
    )
    scenario.result_y = AxisResult(
        drift_ultimate=37,
        braced_ultimate=68,
        drift_service=45,
        braced_service=14,
    )
    scenario.refresh_status()

    output = tmp_path / "acceptance.xlsx"
    export_project_to_excel(template, output, [scenario])

    workbook = load_workbook(output, data_only=False)
    worksheet = workbook["PGA 0,5"]
    assert (scenario.target_sheet, scenario.target_row) == ("PGA 0,5", 11)
    assert [worksheet[cell].value for cell in ("G11", "L11")] == [10, 10]
    assert [worksheet[cell].value for cell in ("O11", "P11", "S11", "T11")] == [38, 70, 46, 14]
    assert [worksheet[cell].value for cell in ("W11", "X11", "AA11", "AB11")] == [37, 68, 45, 14]
    assert workbook["Sheet1"]["D4"].value == "=C4/((3^(1/2)*2))"
    workbook.close()
    assert sha256_file(template) == original_hash
