from pathlib import Path

import pytest

from spatial_ci.manifest.artifacts import ResolvedArtifact
from spatial_ci.manifest.resolver import ResolvedSampleArtifacts
from spatial_ci.manifest.validation import (
    PreHashValidationError,
    validate_pre_hash_sample,
)


def _resolved_artifacts() -> ResolvedSampleArtifacts:
    sample_root = Path("tests/fixtures/manifest/pass2/sample-root/spot-1")
    return ResolvedSampleArtifacts(
        sample_id="spot-1",
        sample_root=sample_root,
        image=ResolvedArtifact(
            artifact_type="image",
            path=sample_root / "image.tiff",
        ),
        spatial_coords=ResolvedArtifact(
            artifact_type="spatial_coords",
            path=sample_root / "outs/spatial/tissue_positions_list.csv",
        ),
        scalefactors=ResolvedArtifact(
            artifact_type="scalefactors",
            path=sample_root / "outs/spatial/scalefactors_json.json",
        ),
        raw_expression=ResolvedArtifact(
            artifact_type="raw_expression",
            path=sample_root / "outs/filtered_feature_bc_matrix.h5",
        ),
        derived_expression=ResolvedArtifact(
            artifact_type="derived_expression",
            path=sample_root / "derived/expression.h5ad",
        ),
    )


def test_validate_pre_hash_sample_rejects_duplicate_required_artifact_paths() -> None:
    resolved = _resolved_artifacts()
    duplicated = resolved.model_copy(
        update={"spatial_coords": resolved.image}
    )

    with pytest.raises(PreHashValidationError, match="distinct"):
        validate_pre_hash_sample(
            {
                "sample_id": "spot-1",
                "cohort_id": "cohort-a",
                "split": "train",
                "resolved_patient_id": "cohort-a::patient-1",
                "patient_id_source": "patient_id",
            },
            resolved_artifacts=duplicated,
        )


def test_validate_pre_hash_sample_rejects_raw_and_derived_conflation() -> None:
    resolved = _resolved_artifacts()
    conflated = resolved.model_copy(
        update={"derived_expression": resolved.raw_expression}
    )

    with pytest.raises(PreHashValidationError, match="raw and derived"):
        validate_pre_hash_sample(
            {
                "sample_id": "spot-1",
                "cohort_id": "cohort-a",
                "split": "train",
                "resolved_patient_id": "cohort-a::patient-1",
                "patient_id_source": "patient_id",
            },
            resolved_artifacts=conflated,
        )


def test_validate_pre_hash_sample_rejects_missing_required_ids() -> None:
    with pytest.raises(PreHashValidationError, match="resolved_patient_id"):
        validate_pre_hash_sample(
            {
                "sample_id": "spot-1",
                "cohort_id": "cohort-a",
                "split": "train",
                "resolved_patient_id": None,
                "patient_id_source": "patient_id",
            },
            resolved_artifacts=_resolved_artifacts(),
        )
