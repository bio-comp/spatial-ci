from pathlib import Path

from pydantic import BaseModel, model_validator

from spatial_ci.contracts.definitions import ArtifactProvenance


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


class ResolvedArtifact(BaseModel):
    """Resolved on-disk artifact candidate before hashing."""

    artifact_type: str
    path: Path


class RejectionRow(BaseModel):
    """One sample-level rejection emitted during pass-2 materialization."""

    sample_id: str
    cohort_id: str
    split: str
    reason: str
    details: str | None = None


class RejectionLedgerArtifact(BaseModel):
    """Deterministic rejection ledger written when pass-2 finds failures."""

    manifest_id: str
    output_path: Path
    n_rejections: int
    rows: list[RejectionRow]

    @model_validator(mode="after")
    def _validate_rejection_count(self) -> "RejectionLedgerArtifact":
        if self.n_rejections != len(self.rows):
            raise ValueError("n_rejections must match len(rows)")
        return self


class MaterializedManifestRow(BaseModel):
    """One final pass-2 manifest row with hashed artifact provenance."""

    sample_id: str
    cohort_id: str
    split: str
    resolved_patient_id: str
    patient_id_source: str
    resolved_specimen_id: str | None = None
    resolved_slide_id: str | None = None
    metadata: dict[str, str | int | float | bool | None]
    image_artifact: ArtifactProvenance
    spatial_coords_artifact: ArtifactProvenance
    scalefactors_artifact: ArtifactProvenance
    raw_expression_artifact: ArtifactProvenance
    derived_expression_artifact: ArtifactProvenance | None = None


class MaterializedManifestArtifact(BaseModel):
    """Frozen final manifest artifact with accepted pass-2 rows."""

    manifest_id: str
    split_contract_id: str
    alignment_contract_id: str
    output_path: Path
    rejection_ledger_path: Path | None = None
    n_rows: int
    rows: list[MaterializedManifestRow]

    @model_validator(mode="after")
    def _validate_row_count(self) -> "MaterializedManifestArtifact":
        if self.n_rows != len(self.rows):
            raise ValueError("n_rows must match len(rows)")
        return self
