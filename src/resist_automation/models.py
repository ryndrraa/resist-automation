from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import RESULT_FIELDS, SCHEMA_VERSION


class AxisResult(BaseModel):
    drift_ultimate: float | None = Field(default=None, ge=0)
    braced_ultimate: float | None = Field(default=None, ge=0)
    drift_service: float | None = Field(default=None, ge=0)
    braced_service: float | None = Field(default=None, ge=0)

    def completed_count(self) -> int:
        return sum(getattr(self, field) is not None for field in RESULT_FIELDS)


class StructureAxis(BaseModel):
    direction: Literal["x", "y"]
    structure_id: str | None = None
    class_name: str | None = None
    bracing_type: str | None = None
    depth_m: float | None = Field(default=None, ge=0)
    depth_cm: float | int | None = Field(default=None, ge=0)
    bay_length: float | None = Field(default=None, ge=0)
    num_bays: int | None = Field(default=None, ge=0)
    num_braced_bays: int | None = Field(default=None, ge=0)
    num_components: int | None = Field(default=None, ge=0)
    centre_of_rigidity: dict[str, Any] = Field(default_factory=dict)
    layout_points: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("structure_id")
    @classmethod
    def normalize_structure_id(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class RSXMetadata(BaseModel):
    version: str | None = None
    country_code: str | None = None
    code_year: str | None = None
    language: str | None = None
    modeller: str | None = None
    file_date: str | None = None
    project: str | None = None
    raw: dict[str, str] = Field(default_factory=dict)


class BuildingData(BaseModel):
    attributes: dict[str, str] = Field(default_factory=dict)
    num_storeys: int | None = Field(default=None, ge=0)
    storey_height: float | None = Field(default=None, ge=0)
    roof_height: float | None = Field(default=None, ge=0)
    area: float | None = Field(default=None, ge=0)
    perimeter_length: float | None = Field(default=None, ge=0)
    perimeter_points: list[dict[str, Any]] = Field(default_factory=list)
    wind_region: str | None = None


class EarthquakeData(BaseModel):
    pga: float = Field(ge=0)
    attributes: dict[str, str] = Field(default_factory=dict)


class ParsedRSX(BaseModel):
    source_path: Path
    metadata: RSXMetadata
    building: BuildingData
    earthquake: EarthquakeData
    structures: dict[Literal["x", "y"], StructureAxis]
    warnings: list[str] = Field(default_factory=list)


class MappingEntry(BaseModel):
    sheet: str
    pga: float
    row: int
    structure_x: str
    structure_y: str

    @field_validator("structure_x", "structure_y")
    @classmethod
    def normalize_id(cls, value: str) -> str:
        return value.strip().upper()


class WorkbookMapping(BaseModel):
    template_path: Path
    entries: list[MappingEntry]

    def find(self, pga: float, structure_x: str, structure_y: str) -> MappingEntry | None:
        x_id, y_id = structure_x.upper(), structure_y.upper()
        for entry in self.entries:
            if abs(entry.pga - pga) < 0.0001 and entry.structure_x == x_id and entry.structure_y == y_id:
                return entry
        return None


class Scenario(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    scenario_id: str
    source_path: Path
    pga: float = Field(ge=0)
    target_sheet: str | None = None
    target_row: int | None = Field(default=None, ge=1)
    structure_x: StructureAxis
    structure_y: StructureAxis
    result_x: AxisResult = Field(default_factory=AxisResult)
    result_y: AxisResult = Field(default_factory=AxisResult)
    status: str = "Belum dipetakan"
    notes: str = ""
    source_mtime_ns: int | None = None
    source_sha256: str | None = None

    def refresh_status(self) -> str:
        if not self.target_sheet or not self.target_row:
            self.status = "Belum dipetakan"
            return self.status
        if self.structure_x.depth_cm is None or self.structure_y.depth_cm is None:
            self.status = "Error"
            return self.status
        completed = self.result_x.completed_count() + self.result_y.completed_count()
        if completed == 0:
            self.status = "Siap diisi"
        elif completed == 8:
            self.status = "Lengkap"
        else:
            self.status = "Sebagian"
        return self.status


class ProjectSession(BaseModel):
    schema_version: int = SCHEMA_VERSION
    name: str
    template_path: Path
    rsx_folder: Path | None = None
    scenarios: list[Scenario] = Field(default_factory=list)
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ValidationIssue(BaseModel):
    severity: Literal["ERROR", "PERINGATAN", "INFO"]
    code: str
    message: str
    scenario_id: str | None = None


class ValidationReport(BaseModel):
    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)


class ExportCellChange(BaseModel):
    sheet: str
    row: int
    cell: str
    old_value: Any = None
    new_value: Any = None


class ExportReport(BaseModel):
    output_path: Path
    backup_path: Path | None = None
    changes: list[ExportCellChange] = Field(default_factory=list)
    exported_scenarios: int = 0
