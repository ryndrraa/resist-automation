from __future__ import annotations

from pathlib import Path

from ..excel.writer import export_project_to_excel
from ..models import ExportReport, ProjectSession, Scenario


class ExportService:
    def export(
        self,
        template_path: Path,
        output_path: Path,
        scenarios: list[Scenario],
        *,
        allow_overwrite: bool = False,
        confirm_high_values: bool = False,
        backup_directory: Path | None = None,
    ) -> ExportReport:
        return export_project_to_excel(
            template_path,
            output_path,
            scenarios,
            allow_overwrite=allow_overwrite,
            allow_over_100=confirm_high_values,
            backup_directory=backup_directory,
        )

    def export_project(
        self,
        project: ProjectSession,
        output_path: Path,
        **options: object,
    ) -> ExportReport:
        return self.export(project.template_path, output_path, project.scenarios, **options)
