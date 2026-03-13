from pathlib import Path

import polars as pl

from spatial_ci.manifest.artifacts import (
    SplitAssignmentArtifact,
    SplitAssignmentRow,
)
from spatial_ci.manifest.config import (
    ManifestBuildConfig,
    ManifestSourceConfig,
    load_manifest_config,
)
from spatial_ci.manifest.identity import derive_resolved_identity
from spatial_ci.manifest.normalize import normalize_manifest_source
from spatial_ci.manifest.splits import assign_patient_splits

OUTPUT_COLUMNS = [
    "sample_id",
    "cohort_id",
    "split",
    "resolved_patient_id",
    "patient_id_source",
    "resolved_specimen_id",
    "resolved_slide_id",
]


class ManifestPipelineError(RuntimeError):
    """Raised when pass-1 manifest construction fails."""


def _read_source_table(source: ManifestSourceConfig) -> pl.DataFrame:
    if source.format == "csv":
        return pl.read_csv(source.path)
    if source.format == "parquet":
        return pl.read_parquet(source.path)
    raise ManifestPipelineError(f"Unsupported source format: {source.format}")


def _normalize_sources(config: ManifestBuildConfig) -> pl.DataFrame:
    frames = [
        normalize_manifest_source(
            _read_source_table(source),
            field_map=source.field_map,
            cohort_id=source.cohort_id,
        )
        for source in config.sources
    ]
    if not frames:
        raise ManifestPipelineError(
            "Manifest build config must define at least one source"
        )
    return pl.concat(frames, how="diagonal_relaxed")


def _validate_unique_sample_ids(frame: pl.DataFrame) -> None:
    duplicate_rows = frame.filter(pl.col("sample_id").is_duplicated())
    if duplicate_rows.height == 0:
        return
    duplicate_ids = sorted(set(duplicate_rows.get_column("sample_id").to_list()))
    duplicate_display = ", ".join(duplicate_ids)
    raise ManifestPipelineError(f"duplicate sample_id: {duplicate_display}")


def build_split_assignments(
    *,
    config_path: Path,
    output_path: Path,
) -> SplitAssignmentArtifact:
    """Build the pass-1 split-assignment artifact and write it to Parquet."""

    config = load_manifest_config(config_path)
    normalized = _normalize_sources(config)
    _validate_unique_sample_ids(normalized)

    resolved = derive_resolved_identity(normalized)
    assigned = assign_patient_splits(
        resolved,
        split_contract_id=config.split_contract.split_contract_id,
        val_fraction=config.split_contract.val_fraction,
        external_holdout_cohorts=config.split_contract.external_holdout_cohorts,
    )

    output_table = assigned.select(OUTPUT_COLUMNS).sort(
        by=["split", "cohort_id", "sample_id"]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_table.write_parquet(output_path)

    rows = [
        SplitAssignmentRow.model_validate(row_dict)
        for row_dict in output_table.to_dicts()
    ]
    return SplitAssignmentArtifact(
        split_contract_id=config.split_contract.split_contract_id,
        output_path=output_path,
        rows=rows,
    )
