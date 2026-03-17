from collections.abc import Mapping
from pathlib import Path

import polars as pl
from pydantic import ValidationError

from spatial_ci.manifest.artifacts import (
    MaterializedManifestArtifact,
    MaterializedManifestRow,
    RejectionLedgerArtifact,
    RejectionRow,
)
from spatial_ci.manifest.config import ManifestOutputConfig, ResolverConfig
from spatial_ci.manifest.hashing import build_artifact_provenance
from spatial_ci.manifest.resolver import (
    ArtifactResolutionError,
    resolve_sample_artifacts,
)
from spatial_ci.manifest.validation import (
    PreHashValidationError,
    validate_pre_hash_sample,
)

MetadataValue = str | int | float | bool | None


class ManifestMaterializationError(RuntimeError):
    """Raised when pass-2 materialization finds fatal sample rejections."""


def _normalize_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if normalized == "":
        return None
    return normalized


def _required_string(row: Mapping[str, object], field_name: str) -> str:
    value = _normalize_string(row.get(field_name))
    if value is None:
        raise ValueError(f"missing required field: {field_name}")
    return value


def _build_metadata(
    row: Mapping[str, object],
    *,
    manifest_config: ManifestOutputConfig,
) -> dict[str, MetadataValue]:
    metadata: dict[str, MetadataValue] = dict(manifest_config.metadata_defaults)
    metadata.setdefault("cohort", _required_string(row, "cohort_id"))
    metadata.setdefault("patient_id", _required_string(row, "resolved_patient_id"))
    return metadata


def _row_sort_key(row: Mapping[str, object]) -> tuple[str, str, str]:
    return (
        _required_string(row, "split"),
        _required_string(row, "cohort_id"),
        _required_string(row, "sample_id"),
    )


def _rejection_sort_key(row: RejectionRow) -> tuple[str, str, str]:
    return (row.split, row.cohort_id, row.sample_id)


def _manifest_sort_key(row: MaterializedManifestRow) -> tuple[str, str, str]:
    return (row.split, row.cohort_id, row.sample_id)


def _rejection_row(
    row: Mapping[str, object],
    *,
    reason: str,
    details: str,
) -> RejectionRow:
    return RejectionRow(
        sample_id=_required_string(row, "sample_id"),
        cohort_id=_required_string(row, "cohort_id"),
        split=_required_string(row, "split"),
        reason=reason,
        details=details,
    )


def _materialize_row(
    row: Mapping[str, object],
    *,
    resolver_config: ResolverConfig,
    manifest_config: ManifestOutputConfig,
) -> MaterializedManifestRow:
    resolved_artifacts = resolve_sample_artifacts(
        row,
        resolver_config=resolver_config,
    )
    validate_pre_hash_sample(
        row,
        resolved_artifacts=resolved_artifacts,
    )
    return MaterializedManifestRow(
        sample_id=_required_string(row, "sample_id"),
        cohort_id=_required_string(row, "cohort_id"),
        split=_required_string(row, "split"),
        resolved_patient_id=_required_string(row, "resolved_patient_id"),
        patient_id_source=_required_string(row, "patient_id_source"),
        resolved_specimen_id=_normalize_string(row.get("resolved_specimen_id")),
        resolved_slide_id=_normalize_string(row.get("resolved_slide_id")),
        metadata=_build_metadata(row, manifest_config=manifest_config),
        image_artifact=build_artifact_provenance(resolved_artifacts.image),
        spatial_coords_artifact=build_artifact_provenance(
            resolved_artifacts.spatial_coords
        ),
        scalefactors_artifact=build_artifact_provenance(resolved_artifacts.scalefactors),
        raw_expression_artifact=build_artifact_provenance(
            resolved_artifacts.raw_expression
        ),
        derived_expression_artifact=(
            build_artifact_provenance(resolved_artifacts.derived_expression)
            if resolved_artifacts.derived_expression is not None
            else None
        ),
    )


def _write_rejection_ledger(
    rows: list[RejectionRow],
    *,
    manifest_id: str,
    output_path: Path,
) -> RejectionLedgerArtifact:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        [row.model_dump(mode="json") for row in rows]
    ).write_parquet(output_path)
    return RejectionLedgerArtifact(
        manifest_id=manifest_id,
        output_path=output_path,
        n_rejections=len(rows),
        rows=rows,
    )


def _write_materialized_manifest(
    rows: list[MaterializedManifestRow],
    *,
    manifest_id: str,
    split_contract_id: str,
    alignment_contract_id: str,
    output_path: Path,
    rejection_ledger_path: Path | None,
) -> MaterializedManifestArtifact:
    if not rows:
        raise ManifestMaterializationError(
            "No accepted rows remained after pass-2 materialization"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        [row.model_dump(mode="json") for row in rows]
    ).write_parquet(output_path)
    return MaterializedManifestArtifact(
        manifest_id=manifest_id,
        split_contract_id=split_contract_id,
        alignment_contract_id=alignment_contract_id,
        output_path=output_path,
        rejection_ledger_path=rejection_ledger_path,
        n_rows=len(rows),
        rows=rows,
    )


def materialize_manifest(
    assigned_frame: pl.DataFrame,
    *,
    output_path: Path,
    split_contract_id: str,
    resolver_config: ResolverConfig,
    manifest_config: ManifestOutputConfig,
    allow_missing: bool,
) -> MaterializedManifestArtifact:
    """Resolve, validate, hash, and write the final pass-2 manifest."""

    accepted_rows: list[MaterializedManifestRow] = []
    rejection_rows: list[RejectionRow] = []

    for row in sorted(assigned_frame.to_dicts(), key=_row_sort_key):
        try:
            accepted_rows.append(
                _materialize_row(
                    row,
                    resolver_config=resolver_config,
                    manifest_config=manifest_config,
                )
            )
        except ArtifactResolutionError as exc:
            rejection_rows.append(
                _rejection_row(
                    row,
                    reason="artifact_resolution_error",
                    details=str(exc),
                )
            )
        except PreHashValidationError as exc:
            rejection_rows.append(
                _rejection_row(
                    row,
                    reason="pre_hash_validation_error",
                    details=str(exc),
                )
            )
        except (ValidationError, ValueError) as exc:
            rejection_rows.append(
                _rejection_row(
                    row,
                    reason="final_manifest_validation_error",
                    details=str(exc),
                )
            )

    rejection_ledger_path: Path | None = None
    if rejection_rows:
        rejection_rows.sort(key=_rejection_sort_key)
        rejection_ledger = _write_rejection_ledger(
            rejection_rows,
            manifest_id=manifest_config.manifest_id,
            output_path=output_path.with_suffix(".rejections.parquet"),
        )
        rejection_ledger_path = rejection_ledger.output_path
        if not allow_missing:
            raise ManifestMaterializationError(
                "Pass-2 materialization wrote rejection ledger to "
                f"{rejection_ledger_path}"
            )

    accepted_rows.sort(key=_manifest_sort_key)
    return _write_materialized_manifest(
        accepted_rows,
        manifest_id=manifest_config.manifest_id,
        split_contract_id=split_contract_id,
        alignment_contract_id=manifest_config.alignment_contract_id,
        output_path=output_path,
        rejection_ledger_path=rejection_ledger_path,
    )
