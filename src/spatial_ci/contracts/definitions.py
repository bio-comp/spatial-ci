from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class TargetDefinition(BaseModel):
    """Frozen definition for target programs and gene sets."""

    target_definition_id: str
    source: str = "MSigDB Hallmark"
    version: str = "v1"
    programs: dict[str, list[str]]
    missing_gene_policy_threshold: float = 0.1  # drop if > 10% genes missing


class ScoringContract(BaseModel):
    """Contract for how target scores are calculated."""

    scoring_contract_id: str
    method: str = "singscore"
    implementation: str = "R/Bioconductor"
    single_sample: bool = True
    output_format: str = "parquet"


class AlignmentMode(str, Enum):
    SPOT_PLUS_CONTEXT = "spot_plus_context"
    EXACT_SPOT = "exact_spot"


class AlignmentContract(BaseModel):
    """Contract for image-to-spot alignment and crop parameters."""

    alignment_contract_id: str
    target_mpp: float = 0.5
    tile_size_px: int = 224
    extraction_mode: AlignmentMode = AlignmentMode.SPOT_PLUS_CONTEXT


class SplitStrategy(str, Enum):
    PATIENT_LEVEL = "patient_level"
    SLIDE_LEVEL = "slide_level"


class SplitContract(BaseModel):
    """Contract for deterministic train/val/test splits."""

    split_contract_id: str
    strategy: SplitStrategy = SplitStrategy.PATIENT_LEVEL
    deterministic: bool = True
    val_fraction: float = 0.2
    external_holdout_cohorts: list[str] = []


class BaselineContract(BaseModel):
    """Contract for simple baseline models that learning models must beat."""

    baseline_contract_id: str
    required_baselines: list[str] = [
        "global_train_mean",
        "mean_by_train_cohort",
        "knn_on_embeddings",
        "ridge_probe",
    ]


class BootstrapContract(BaseModel):
    """Contract for clustered uncertainty estimation."""

    bootstrap_contract_id: str
    n_bootstrap: int = 1000
    cluster_by: str = "patient_id"


class ArtifactProvenance(BaseModel):
    """Minimal provenance required for manifest-tracked artifacts."""

    path: Path
    hash_sha256: str | None = None
    artifact_type: str


ManifestMetadataValue = str | int | float | bool | None


class SampleManifestRow(BaseModel):
    """A single row in the materialized sample manifest."""

    sample_id: str
    cohort_id: str
    split: str
    resolved_patient_id: str
    patient_id_source: str
    resolved_specimen_id: str | None = None
    resolved_slide_id: str | None = None
    metadata: dict[str, ManifestMetadataValue]
    image_artifact: ArtifactProvenance
    spatial_coords_artifact: ArtifactProvenance
    scalefactors_artifact: ArtifactProvenance
    raw_expression_artifact: ArtifactProvenance
    derived_expression_artifact: ArtifactProvenance | None = None


class SampleManifest(BaseModel):
    """Full materialized manifest for a dataset."""

    manifest_id: str
    split_contract_id: str
    alignment_contract_id: str
    rows: list[SampleManifestRow]


class EvaluationCertificate(BaseModel):
    """Decision-grade report for a model run."""

    run_id: str
    target_definition_id: str
    scoring_contract_id: str
    split_contract_id: str
    alignment_contract_id: str
    baseline_contract_id: str
    bootstrap_contract_id: str
    primary_intervention_axis: str
    metrics: dict[str, dict[str, float]]  # target -> metric -> value
    uncertainty: dict[str, dict[str, list[float]]]  # target -> metric -> [low, high]
    baseline_comparisons: dict[str, dict[str, float]]
    leakage_status: str = "audit_passed"
    notes: str | None = None
