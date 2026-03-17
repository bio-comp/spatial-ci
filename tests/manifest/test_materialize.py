from pathlib import Path

import polars as pl
import pytest

from spatial_ci.manifest.pipeline import (
    ManifestPipelineError,
    build_materialized_manifest,
)


def test_build_materialized_manifest_writes_final_manifest_when_clean(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "manifest.parquet"

    artifact = build_materialized_manifest(
        config_path=Path("tests/fixtures/manifest/pass2/config_materialize.yaml"),
        output_path=output_path,
        allow_missing=False,
    )

    assignments_path = output_path.with_suffix(".assignments.parquet")
    rejections_path = output_path.with_suffix(".rejections.parquet")
    table = pl.read_parquet(output_path)

    assert assignments_path.exists()
    assert output_path.exists()
    assert not rejections_path.exists()
    assert artifact.manifest_id == "breast_visium_manifest_v1"
    assert table.select(["split", "cohort_id", "sample_id"]).rows() == sorted(
        table.select(["split", "cohort_id", "sample_id"]).rows()
    )


def test_build_materialized_manifest_writes_rejection_ledger_and_fails_by_default(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "manifest.parquet"

    with pytest.raises(ManifestPipelineError, match="rejection ledger"):
        build_materialized_manifest(
            config_path=Path(
                "tests/fixtures/manifest/pass2/config_materialize_missing.yaml"
            ),
            output_path=output_path,
            allow_missing=False,
        )

    assert output_path.with_suffix(".assignments.parquet").exists()
    assert output_path.with_suffix(".rejections.parquet").exists()
    assert not output_path.exists()


def test_build_materialized_manifest_allows_missing_when_requested(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "manifest.parquet"

    artifact = build_materialized_manifest(
        config_path=Path("tests/fixtures/manifest/pass2/config_materialize_missing.yaml"),
        output_path=output_path,
        allow_missing=True,
    )

    rejections_path = output_path.with_suffix(".rejections.parquet")
    table = pl.read_parquet(output_path)
    rejection_table = pl.read_parquet(rejections_path)

    assert output_path.exists()
    assert rejections_path.exists()
    assert artifact.n_rows == 1
    assert table.height == 1
    assert rejection_table.height == 1
    assert rejection_table.get_column("sample_id").to_list() == ["spot-missing"]
