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


def test_build_split_assignments_has_no_leakage_report_when_clean(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "assignments.parquet"
    artifact = build_split_assignments(
        config_path=Path("tests/fixtures/manifest/pass1/config_basic.yaml"),
        output_path=output_path,
    )

    assert artifact.leakage_report_path is None
    assert not output_path.with_suffix(".leakage.parquet").exists()


def test_build_split_assignments_writes_leakage_report_and_fails(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "assignments.parquet"

    with pytest.raises(ManifestPipelineError, match="Leakage detected"):
        build_split_assignments(
            config_path=Path("tests/fixtures/manifest/pass1/config_leakage.yaml"),
            output_path=output_path,
        )

    leakage_path = output_path.with_suffix(".leakage.parquet")
    assert output_path.exists()
    assert leakage_path.exists()

    leakage_table = pl.read_parquet(leakage_path)
    assert leakage_table.columns == [
        "split_left",
        "split_right",
        "audit_column",
        "overlapping_id",
    ]
    assert leakage_table.rows() == [
        ("train", "val", "resolved_slide_id", "cohort-a::shared-slide")
    ]
