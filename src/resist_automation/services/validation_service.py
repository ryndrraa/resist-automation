from __future__ import annotations

from collections import Counter

from ..models import ProjectSession, Scenario, ValidationIssue, ValidationReport


class ValidationService:
    def validate_scenarios(self, scenarios: list[Scenario]) -> ValidationReport:
        issues: list[ValidationIssue] = []
        counts: Counter[str] = Counter()
        targets: dict[tuple[str, int], str] = {}

        for scenario in scenarios:
            if scenario.status != "Sudah diekspor":
                scenario.refresh_status()
            counts[scenario.status] += 1
            if scenario.target_sheet and scenario.target_row:
                target = (scenario.target_sheet, scenario.target_row)
                if target in targets:
                    issues.append(
                        ValidationIssue(
                            severity="ERROR",
                            code="DUPLICATE_TARGET",
                            scenario_id=scenario.scenario_id,
                            message=(
                                f"Target {scenario.target_sheet} baris {scenario.target_row} juga dipakai "
                                f"oleh {targets[target]}."
                            ),
                        )
                    )
                targets[target] = scenario.scenario_id

            if scenario.status == "Belum dipetakan":
                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="UNMAPPED_SCENARIO",
                        scenario_id=scenario.scenario_id,
                        message="PGA atau kombinasi struktur belum dipetakan.",
                    )
                )
            elif scenario.status == "Error":
                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="INVALID_SCENARIO",
                        scenario_id=scenario.scenario_id,
                        message="Dimensi struktur X/Y belum lengkap.",
                    )
                )
            elif scenario.status in {"Siap diisi", "Sebagian"}:
                issues.append(
                    ValidationIssue(
                        severity="PERINGATAN",
                        code="INCOMPLETE_RESULTS",
                        scenario_id=scenario.scenario_id,
                        message=f"Hasil masih berstatus {scenario.status}.",
                    )
                )

            values = [
                scenario.result_x.drift_ultimate,
                scenario.result_x.braced_ultimate,
                scenario.result_x.drift_service,
                scenario.result_x.braced_service,
                scenario.result_y.drift_ultimate,
                scenario.result_y.braced_ultimate,
                scenario.result_y.drift_service,
                scenario.result_y.braced_service,
            ]
            if any(value is not None and value > 100 for value in values):
                issues.append(
                    ValidationIssue(
                        severity="PERINGATAN",
                        code="VALUE_OVER_100",
                        scenario_id=scenario.scenario_id,
                        message="Ada nilai hasil di atas 100 dan perlu konfirmasi sebelum ekspor.",
                    )
                )

        return ValidationReport(
            valid=not any(issue.severity == "ERROR" for issue in issues),
            issues=issues,
            counts=dict(counts),
        )

    def validate_project(self, project: ProjectSession) -> ValidationReport:
        return self.validate_scenarios(project.scenarios)
