from pathlib import Path

import polars as pl

from spatial_ci.manifest.artifacts import LeakageReportArtifact, LeakageReportRow

AUDIT_COLUMNS = [
    "resolved_patient_id",
    "resolved_specimen_id",
    "resolved_slide_id",
]
AUDITED_SPLIT_PAIRS = [
    ("train", "val"),
    ("train", "test_external"),
    ("val", "test_external"),
]


def _split_ids(
    frame: pl.DataFrame,
    *,
    split_name: str,
    audit_column: str,
) -> set[str]:
    split_frame = frame.filter(pl.col("split") == split_name)
    if split_frame.height == 0:
        return set()

    id_values = split_frame.get_column(audit_column).drop_nulls().to_list()
    return {str(value) for value in id_values}


def build_leakage_report(
    frame: pl.DataFrame,
    *,
    split_contract_id: str,
    report_path: Path,
) -> LeakageReportArtifact:
    """Audit overlap across the required split pairs and identity columns."""

    findings: list[LeakageReportRow] = []
    for audit_column in AUDIT_COLUMNS:
        for split_left, split_right in AUDITED_SPLIT_PAIRS:
            overlapping_ids = sorted(
                _split_ids(frame, split_name=split_left, audit_column=audit_column)
                & _split_ids(frame, split_name=split_right, audit_column=audit_column)
            )
            for overlapping_id in overlapping_ids:
                findings.append(
                    LeakageReportRow(
                        split_left=split_left,
                        split_right=split_right,
                        audit_column=audit_column,
                        overlapping_id=overlapping_id,
                    )
                )

    findings.sort(
        key=lambda row: (
            row.audit_column,
            row.split_left,
            row.split_right,
            row.overlapping_id,
        )
    )
    return LeakageReportArtifact(
        split_contract_id=split_contract_id,
        report_path=report_path,
        n_findings=len(findings),
        rows=findings,
    )
