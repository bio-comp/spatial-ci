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
    rows: list[SplitAssignmentRow]
