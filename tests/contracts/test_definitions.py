# mypy: disable-error-code=untyped-decorator

from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from spatial_ci.contracts.definitions import (
    ArtifactProvenance,
    SampleManifestRow,
    TargetDefinition,
)


def test_target_definition_basic() -> None:
    """Basic sanity check for TargetDefinition."""
    programs = {
        "HALLMARK_HYPOXIA": ["GENE1", "GENE2"],
        "HALLMARK_G2M_CHECKPOINT": ["GENE3", "GENE4"],
    }
    target = TargetDefinition(target_definition_id="test_v1", programs=programs)
    assert target.target_definition_id == "test_v1"
    assert target.programs == programs
    assert target.missing_gene_policy_threshold == 0.1


def test_sample_manifest_row_accepts_pass2_shape() -> None:
    row = SampleManifestRow(
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

    assert row.sample_id == "spot-1"
    assert row.raw_expression_artifact.artifact_type == "raw_expression"


@given(
    target_id=st.text(min_size=1),
    programs=st.dictionaries(
        keys=st.text(min_size=1),
        values=st.lists(st.text(min_size=1), min_size=1),
        min_size=1,
    ),
    threshold=st.floats(min_value=0.0, max_value=1.0),
)
def test_target_definition_hypothesis(
    target_id: str,
    programs: dict[str, list[str]],
    threshold: float,
) -> None:
    """Property-based test for TargetDefinition."""
    target = TargetDefinition(
        target_definition_id=target_id,
        programs=programs,
        missing_gene_policy_threshold=threshold,
    )
    assert target.target_definition_id == target_id
    assert target.programs == programs
    assert target.missing_gene_policy_threshold == threshold
