from pathlib import Path

import pytest
from pydantic import ValidationError

from spatial_ci.contracts.definitions import ArtifactProvenance
from spatial_ci.manifest.artifacts import (
    MaterializedManifestArtifact,
    MaterializedManifestRow,
    RejectionLedgerArtifact,
    RejectionRow,
    ResolvedArtifact,
)


def test_resolved_artifact_model_tracks_required_resolution_fields() -> None:
    artifact = ResolvedArtifact(
        artifact_type="image",
        path=Path("sample/image.tiff"),
    )

    assert artifact.artifact_type == "image"
    assert artifact.path == Path("sample/image.tiff")


def test_rejection_ledger_artifact_validates_rejection_count() -> None:
    row = RejectionRow(
        sample_id="spot-1",
        cohort_id="cohort-a",
        split="train",
        reason="missing_required_artifact",
    )

    ledger = RejectionLedgerArtifact(
        manifest_id="manifest-v1",
        output_path=Path("manifest.rejections.parquet"),
        n_rejections=1,
        rows=[row],
    )

    assert ledger.rows == [row]

    with pytest.raises(ValidationError, match="n_rejections"):
        RejectionLedgerArtifact(
            manifest_id="manifest-v1",
            output_path=Path("manifest.rejections.parquet"),
            n_rejections=0,
            rows=[row],
        )


def test_materialized_manifest_row_accepts_expected_fields() -> None:
    image_artifact = ArtifactProvenance(
        path=Path("sample/image.tiff"),
        hash_sha256="a" * 64,
        artifact_type="image",
    )
    spatial_coords_artifact = ArtifactProvenance(
        path=Path("sample/tissue_positions.csv"),
        hash_sha256="b" * 64,
        artifact_type="spatial_coords",
    )
    scalefactors_artifact = ArtifactProvenance(
        path=Path("sample/scalefactors_json.json"),
        hash_sha256="c" * 64,
        artifact_type="scalefactors",
    )
    raw_expression_artifact = ArtifactProvenance(
        path=Path("sample/filtered_feature_bc_matrix.h5"),
        hash_sha256="d" * 64,
        artifact_type="raw_expression",
    )

    row = MaterializedManifestRow(
        sample_id="spot-1",
        cohort_id="cohort-a",
        split="train",
        resolved_patient_id="cohort-a::patient-1",
        patient_id_source="patient_id",
        resolved_specimen_id="cohort-a::specimen-1",
        resolved_slide_id="cohort-a::slide-1",
        metadata={
            "cohort": "cohort-a",
            "assay_platform": "visium",
            "tissue_type": "breast",
            "patient_id": "cohort-a::patient-1",
        },
        image_artifact=image_artifact,
        spatial_coords_artifact=spatial_coords_artifact,
        scalefactors_artifact=scalefactors_artifact,
        raw_expression_artifact=raw_expression_artifact,
        derived_expression_artifact=None,
    )

    assert row.metadata["assay_platform"] == "visium"
    assert row.derived_expression_artifact is None


def test_materialized_manifest_artifact_validates_row_count() -> None:
    row = MaterializedManifestRow(
        sample_id="spot-1",
        cohort_id="cohort-a",
        split="train",
        resolved_patient_id="cohort-a::patient-1",
        patient_id_source="patient_id",
        resolved_specimen_id=None,
        resolved_slide_id=None,
        metadata={"cohort": "cohort-a"},
        image_artifact=ArtifactProvenance(
            path=Path("sample/image.tiff"),
            hash_sha256="a" * 64,
            artifact_type="image",
        ),
        spatial_coords_artifact=ArtifactProvenance(
            path=Path("sample/tissue_positions.csv"),
            hash_sha256="b" * 64,
            artifact_type="spatial_coords",
        ),
        scalefactors_artifact=ArtifactProvenance(
            path=Path("sample/scalefactors_json.json"),
            hash_sha256="c" * 64,
            artifact_type="scalefactors",
        ),
        raw_expression_artifact=ArtifactProvenance(
            path=Path("sample/filtered_feature_bc_matrix.h5"),
            hash_sha256="d" * 64,
            artifact_type="raw_expression",
        ),
        derived_expression_artifact=None,
    )

    artifact = MaterializedManifestArtifact(
        manifest_id="manifest-v1",
        split_contract_id="split-v1",
        alignment_contract_id="alignment-v1",
        output_path=Path("manifest.parquet"),
        rejection_ledger_path=None,
        n_rows=1,
        rows=[row],
    )

    assert artifact.rows == [row]

    with pytest.raises(ValidationError, match="n_rows"):
        MaterializedManifestArtifact(
            manifest_id="manifest-v1",
            split_contract_id="split-v1",
            alignment_contract_id="alignment-v1",
            output_path=Path("manifest.parquet"),
            rejection_ledger_path=None,
            n_rows=0,
            rows=[row],
        )
