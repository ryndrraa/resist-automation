"""Entry point CLI untuk core RESIST Automation.

GUI sengaja belum diaktifkan pada fase ini. Jalankan ``python app.py --help``
untuk melihat alur demo dan perintah validasi yang tersedia.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from resist_automation.constants import RUNTIME_DATA_ROOT, ensure_runtime_directories  # noqa: E402
from resist_automation.excel.reader import read_workbook_mapping  # noqa: E402
from resist_automation.excel.validator import validate_workbook  # noqa: E402
from resist_automation.models import AxisResult  # noqa: E402
from resist_automation.rsx.mapper import scenario_from_parsed  # noqa: E402
from resist_automation.rsx.parser import parse_rsx  # noqa: E402
from resist_automation.services.export_service import ExportService  # noqa: E402
from resist_automation.services.import_service import ImportService  # noqa: E402
from resist_automation.utils.logger import configure_logging  # noqa: E402


def _inspect_rsx(path: Path) -> int:
    parsed = parse_rsx(path)
    print(json.dumps(parsed.model_dump(mode="json"), indent=2, ensure_ascii=False))
    return 0


def _scan_folder(path: Path, recursive: bool) -> int:
    service = ImportService()
    report = service.scan_folder(path, recursive=recursive)
    print(f"Berhasil: {len(report.parsed)} file")
    for item in report.parsed:
        print(f"- {item.source_path.name}: PGA {item.earthquake.pga}")
    for failure in report.failures:
        print(f"- ERROR {failure.path.name}: {failure.message}")
    return 1 if report.failures else 0


def _validate_template(path: Path) -> int:
    report = validate_workbook(path)
    for issue in report.issues:
        print(f"[{issue.severity}] {issue.message}")
    if report.valid:
        mapping = read_workbook_mapping(path)
        print(f"Template valid: {len(mapping.entries)} kombinasi terbaca")
        return 0
    return 1


def _demo_export(rsx: Path, template: Path, output: Path) -> int:
    """Menjalankan contoh integrasi dengan angka acceptance test dari PRD."""

    parsed = parse_rsx(rsx)
    workbook_mapping = read_workbook_mapping(template)
    scenario = scenario_from_parsed(parsed, workbook_mapping)
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
    report = ExportService().export(template, output, [scenario])
    print(f"Ekspor berhasil: {report.output_path}")
    print(f"Sel ditulis: {len(report.changes)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RESIST Automation Desktop")
    subparsers = parser.add_subparsers(dest="command")

    inspect_parser = subparsers.add_parser("inspect-rsx", help="Baca dan tampilkan ringkasan RSX")
    inspect_parser.add_argument("path", type=Path)

    scan_parser = subparsers.add_parser("scan", help="Pindai folder berisi RSX")
    scan_parser.add_argument("path", type=Path)
    scan_parser.add_argument("--recursive", action="store_true")

    workbook_parser = subparsers.add_parser("validate-template", help="Validasi workbook template")
    workbook_parser.add_argument("path", type=Path)

    demo_parser = subparsers.add_parser("demo-export", help="Jalankan acceptance test PRD ke workbook baru")
    demo_parser.add_argument(
        "--rsx",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "0.5 BFCTST-BFCTST.rsx",
    )
    demo_parser.add_argument(
        "--template",
        type=Path,
        default=ROOT / "Lembar Kerja Software RESIST - Unit Eficiency.xlsx",
    )
    demo_parser.add_argument("--output", type=Path, default=ROOT / "output" / "demo-resist.xlsx")
    return parser


def main(argv: list[str] | None = None) -> int:
    ensure_runtime_directories()
    configure_logging(RUNTIME_DATA_ROOT / "logs")
    args = build_parser().parse_args(argv)
    try:
        if args.command is None:
            from resist_automation.ui.main_window import run_gui

            run_gui()
            return 0
        if args.command == "inspect-rsx":
            return _inspect_rsx(args.path)
        if args.command == "scan":
            return _scan_folder(args.path, args.recursive)
        if args.command == "validate-template":
            return _validate_template(args.path)
        if args.command == "demo-export":
            return _demo_export(args.rsx, args.template, args.output)
    except Exception as exc:  # Batas CLI: jangan tampilkan traceback mentah ke pengguna.
        print(f"Gagal: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
