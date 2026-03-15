from pathlib import Path

from pydantic import BaseModel


class SplitAssignmentRow(BaseModel):
    """One pass-1 split-assignment row at sample grain."""

    sample_id: str
    cohort_id: str
    split: str
    resolved_patient_id: str
    patient_id_source: str
    resolved_specimen_id: str | None = None
    resolved_slide_id: str | None = None


class SplitAssignmentArtifact(BaseModel):
    """Frozen split-assignment artifact metadata."""

    split_contract_id: str
    output_path: Path
    leakage_report_path: Path | None = None
    rows: list[SplitAssignmentRow]


class LeakageReportRow(BaseModel):
    """One fatal leakage finding between two audited splits."""

    split_left: str
    split_right: str
    audit_column: str
    overlapping_id: str


class LeakageReportArtifact(BaseModel):
    """Deterministic report of overlap findings across audited splits."""

    split_contract_id: str
    report_path: Path
    n_findings: int
    rows: list[LeakageReportRow]
