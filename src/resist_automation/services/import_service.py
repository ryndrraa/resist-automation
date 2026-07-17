from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from pydantic import BaseModel, Field

from ..exceptions import RSXError
from ..models import ParsedRSX, Scenario, WorkbookMapping
from ..rsx.mapper import scenario_from_parsed
from ..rsx.parser import parse_rsx


class ImportFailure(BaseModel):
    path: Path
    message: str


class ImportReport(BaseModel):
    parsed: list[ParsedRSX] = Field(default_factory=list)
    failures: list[ImportFailure] = Field(default_factory=list)


class ScenarioImportReport(BaseModel):
    scenarios: list[Scenario] = Field(default_factory=list)
    failures: list[ImportFailure] = Field(default_factory=list)


class ImportService:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rsx-import")

    def import_file(self, path: Path) -> ParsedRSX:
        return parse_rsx(path)

    def scan_folder(self, folder: Path, *, recursive: bool = False) -> ImportReport:
        folder = Path(folder).expanduser().resolve()
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"Folder RSX tidak ditemukan: {folder}")
        pattern = "**/*.rsx" if recursive else "*.rsx"
        paths = sorted(folder.glob(pattern), key=lambda item: item.name.casefold())
        report = ImportReport()
        for path in paths:
            try:
                report.parsed.append(parse_rsx(path))
            except (RSXError, OSError, ValueError) as exc:
                report.failures.append(ImportFailure(path=path, message=str(exc)))
        report.parsed.sort(key=lambda item: (item.earthquake.pga, item.source_path.name.casefold()))
        return report

    def scan_folder_async(self, folder: Path, *, recursive: bool = False) -> Future[ImportReport]:
        return self._executor.submit(self.scan_folder, folder, recursive=recursive)

    def import_scenarios(
        self,
        folder: Path,
        workbook_mapping: WorkbookMapping,
        *,
        recursive: bool = False,
    ) -> ScenarioImportReport:
        parsed_report = self.scan_folder(folder, recursive=recursive)
        scenarios = [scenario_from_parsed(item, workbook_mapping) for item in parsed_report.parsed]
        scenarios.sort(
            key=lambda item: (
                item.pga,
                item.target_row if item.target_row is not None else 999,
                item.source_path.name.casefold(),
            )
        )
        return ScenarioImportReport(scenarios=scenarios, failures=parsed_report.failures)

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
