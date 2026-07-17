from __future__ import annotations

from pathlib import Path

from ..excel.reader import read_workbook_mapping
from ..models import AxisResult, ProjectSession, Scenario
from ..rsx.mapper import scenario_from_parsed
from ..services.import_service import ImportFailure, ImportService
from ..services.validation_service import ValidationService
from .serializer import load_session, save_session


class ProjectService:
    def __init__(self) -> None:
        self.importer = ImportService()
        self.validator = ValidationService()

    def new_project(self, name: str, template_path: Path, rsx_folder: Path | None = None) -> ProjectSession:
        read_workbook_mapping(template_path)
        return ProjectSession(name=name, template_path=template_path, rsx_folder=rsx_folder)

    def import_paths(
        self,
        project: ProjectSession,
        paths: list[Path],
    ) -> tuple[list[Scenario], list[ImportFailure]]:
        mapping = read_workbook_mapping(project.template_path)
        added: list[Scenario] = []
        failures: list[ImportFailure] = []
        known = {scenario.source_path.resolve() for scenario in project.scenarios}
        for path in paths:
            try:
                parsed = self.importer.import_file(path)
                if parsed.source_path.resolve() in known:
                    continue
                scenario = scenario_from_parsed(parsed, mapping)
                project.scenarios.append(scenario)
                known.add(parsed.source_path.resolve())
                added.append(scenario)
            except Exception as exc:
                failures.append(ImportFailure(path=path, message=str(exc)))
        project.scenarios.sort(
            key=lambda item: (
                item.pga,
                item.target_row if item.target_row is not None else 999,
                item.source_path.name.casefold(),
            )
        )
        return added, failures

    def set_results(
        self,
        scenario: Scenario,
        result_x: AxisResult,
        result_y: AxisResult,
    ) -> None:
        scenario.result_x = result_x
        scenario.result_y = result_y
        scenario.refresh_status()

    def save(self, project: ProjectSession, path: Path) -> Path:
        return save_session(project, path)

    def open(self, path: Path) -> ProjectSession:
        return load_session(path)
