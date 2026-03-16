from pathlib import Path

from spatial_ci.manifest.artifacts import SplitAssignmentRow
from spatial_ci.manifest.config import load_manifest_config


def test_load_manifest_config_reads_yaml_fixture() -> None:
    config = load_manifest_config(
        Path("tests/fixtures/manifest/pass1/config_basic.yaml")
    )
    assert config.split_contract.split_contract_id == "breast_visium_split_v1"
    assert config.sources[0].field_map["sample"] == "sample_id"


def test_load_manifest_config_reads_pass2_resolver_settings() -> None:
    config = load_manifest_config(
        Path("tests/fixtures/manifest/pass2/config_materialize.yaml")
    )

    assert config.manifest is not None
    assert config.resolver is not None
    assert config.manifest.manifest_id == "breast_visium_manifest_v1"
    assert config.manifest.alignment_contract_id == "visium_alignment_v1"
    assert config.resolver.sample_path_field == "sample_path"
    assert config.resolver.sample_roots == (
        Path("tests/fixtures/manifest/pass2/sample-root"),
    )
    assert config.resolver.artifact_candidates.image == (
        Path("image.tiff"),
        Path("outs/spatial/tissue_hires_image.png"),
    )
    assert config.resolver.artifact_candidates.derived_expression == (
        Path("derived/expression.h5ad"),
    )


def test_split_assignment_artifact_model_requires_expected_fields() -> None:
    row = SplitAssignmentRow(
        sample_id="spot-1",
        cohort_id="cohort-a",
        split="train",
        resolved_patient_id="cohort-a::patient-1",
        patient_id_source="patient_id",
        resolved_specimen_id=None,
        resolved_slide_id=None,
    )
    assert row.sample_id == "spot-1"
