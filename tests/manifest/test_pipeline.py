from pathlib import Path

import polars as pl
import pytest

from spatial_ci.manifest.pipeline import ManifestPipelineError, build_split_assignments


def test_build_split_assignments_writes_sorted_parquet(tmp_path: Path) -> None:
    output_path = tmp_path / "assignments.parquet"
    artifact = build_split_assignments(
        config_path=Path("tests/fixtures/manifest/pass1/config_basic.yaml"),
        output_path=output_path,
    )
    table = pl.read_parquet(output_path)
    assert output_path.exists()
    assert table.columns == [
        "sample_id",
        "cohort_id",
        "split",
        "resolved_patient_id",
        "patient_id_source",
        "resolved_specimen_id",
        "resolved_slide_id",
    ]
    assert table.select(["split", "cohort_id", "sample_id"]).rows() == sorted(
        table.select(["split", "cohort_id", "sample_id"]).rows()
    )
    assert artifact.split_contract_id == "breast_visium_split_v1"


def test_build_split_assignments_rejects_duplicate_sample_id(tmp_path: Path) -> None:
    with pytest.raises(ManifestPipelineError, match="duplicate sample_id"):
        build_split_assignments(
            config_path=Path("tests/fixtures/manifest/pass1/config_duplicate.yaml"),
            output_path=tmp_path / "assignments.parquet",
        )
