from __future__ import annotations

from ..models import ParsedRSX, ValidationIssue, ValidationReport


def validate_parsed_rsx(parsed: ParsedRSX) -> ValidationReport:
    issues: list[ValidationIssue] = []
    if not any(abs(parsed.earthquake.pga - supported) < 0.0001 for supported in (0.4, 0.5)):
        issues.append(
            ValidationIssue(
                severity="ERROR",
                code="UNSUPPORTED_PGA",
                message=f"PGA {parsed.earthquake.pga:g} tidak didukung; gunakan 0,4 atau 0,5.",
            )
        )
    for axis in ("x", "y"):
        structure = parsed.structures[axis]
        if structure.depth_cm is None:
            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="MISSING_DEPTH",
                    message=f"Dimensi brace sumbu {axis.upper()} tidak ditemukan.",
                )
            )
    for warning in parsed.warnings:
        issues.append(ValidationIssue(severity="PERINGATAN", code="RSX_WARNING", message=warning))
    return ValidationReport(
        valid=not any(issue.severity == "ERROR" for issue in issues),
        issues=issues,
    )
