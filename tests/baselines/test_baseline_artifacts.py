from pathlib import Path

import pytest
from pydantic import ValidationError

from spatial_ci.baselines.artifacts import (
    BaselineName,
    BaselinePredictionArtifact,
    BaselinePredictionRow,
    read_baseline_prediction_artifact,
    write_baseline_prediction_artifact,
)


def test_baseline_prediction_row_accepts_expected_fields() -> None:
    row = BaselinePredictionRow(
        observation_id="obs-1",
        sample_id="sample-1",
        cohort_id="cohort-a",
        split="val",
        program_name="HALLMARK_HYPOXIA",
        baseline_name=BaselineName.GLOBAL_TRAIN_MEAN,
        predicted_score=0.42,
    )

    assert row.baseline_name is BaselineName.GLOBAL_TRAIN_MEAN


def test_baseline_prediction_artifact_validates_row_count() -> None:
    row = BaselinePredictionRow(
        observation_id="obs-1",
        sample_id="sample-1",
        cohort_id="cohort-a",
        split="val",
        program_name="HALLMARK_HYPOXIA",
        baseline_name=BaselineName.GLOBAL_TRAIN_MEAN,
        predicted_score=0.42,
    )

    artifact = BaselinePredictionArtifact(
        run_id="baseline-run-1",
        baseline_contract_id="mean_baselines_v0",
        split_contract_id="breast_visium_split_v1",
        target_definition_id="breast_visium_hallmarks_v1",
        scoring_contract_id="singscore_r_v1",
        manifest_id="breast_manifest_v1",
        source_score_artifact_path="scores.parquet",
        source_score_artifact_hash="a" * 64,
        source_manifest_path="manifest.parquet",
        source_manifest_hash="b" * 64,
        n_rows=1,
        rows=(row,),
    )

    assert artifact.rows == (row,)

    with pytest.raises(ValidationError, match="n_rows"):
        BaselinePredictionArtifact(
            run_id="baseline-run-1",
            baseline_contract_id="mean_baselines_v0",
            split_contract_id="breast_visium_split_v1",
            target_definition_id="breast_visium_hallmarks_v1",
            scoring_contract_id="singscore_r_v1",
            manifest_id="breast_manifest_v1",
            source_score_artifact_path="scores.parquet",
            source_score_artifact_hash="a" * 64,
            source_manifest_path="manifest.parquet",
            source_manifest_hash="b" * 64,
            n_rows=0,
            rows=(row,),
        )


def test_baseline_prediction_artifact_roundtrips_through_parquet(
    tmp_path: Path,
) -> None:
    artifact = BaselinePredictionArtifact(
        run_id="baseline-run-1",
        baseline_contract_id="mean_baselines_v0",
        split_contract_id="breast_visium_split_v1",
        target_definition_id="breast_visium_hallmarks_v1",
        scoring_contract_id="singscore_r_v1",
        manifest_id=None,
        source_score_artifact_path="scores.parquet",
        source_score_artifact_hash="a" * 64,
        source_manifest_path="manifest.parquet",
        source_manifest_hash="b" * 64,
        n_rows=2,
        rows=(
            BaselinePredictionRow(
                observation_id="obs-1",
                sample_id="sample-1",
                cohort_id="cohort-a",
                split="train",
                program_name="HALLMARK_HYPOXIA",
                baseline_name=BaselineName.GLOBAL_TRAIN_MEAN,
                predicted_score=0.42,
            ),
            BaselinePredictionRow(
                observation_id="obs-1",
                sample_id="sample-1",
                cohort_id="cohort-a",
                split="train",
                program_name="HALLMARK_HYPOXIA",
                baseline_name=BaselineName.MEAN_BY_TRAIN_COHORT,
                predicted_score=0.43,
            ),
        ),
    )
    path = tmp_path / "baseline_predictions.parquet"

    write_baseline_prediction_artifact(artifact, path)
    observed = read_baseline_prediction_artifact(path)

    assert observed == artifact


def test_baseline_prediction_artifact_roundtrips_ridge_alpha_metadata(
    tmp_path: Path,
) -> None:
    artifact = BaselinePredictionArtifact(
        run_id="baseline-run-1",
        baseline_contract_id="standard_baselines_v1",
        split_contract_id="breast_visium_split_v1",
        target_definition_id="breast_visium_hallmarks_v1",
        scoring_contract_id="singscore_r_v1",
        manifest_id="breast_manifest_v1",
        source_score_artifact_path="scores.parquet",
        source_score_artifact_hash="a" * 64,
        source_manifest_path="manifest.parquet",
        source_manifest_hash="b" * 64,
        ridge_probe_selected_alpha_by_program={"HALLMARK_HYPOXIA": 0.1},
        n_rows=1,
        rows=(
            BaselinePredictionRow(
                observation_id="obs-1",
                sample_id="sample-1",
                cohort_id="cohort-a",
                split="val",
                program_name="HALLMARK_HYPOXIA",
                baseline_name=BaselineName.RIDGE_PROBE,
                predicted_score=0.42,
            ),
        ),
    )
    path = tmp_path / "baseline_predictions.parquet"

    write_baseline_prediction_artifact(artifact, path)
    observed = read_baseline_prediction_artifact(path)

    assert observed == artifact


def test_baseline_prediction_artifact_rejects_ridge_rows_without_alpha_metadata(
) -> None:
    with pytest.raises(ValidationError, match="ridge_probe_selected_alpha_by_program"):
        BaselinePredictionArtifact(
            run_id="baseline-run-1",
            baseline_contract_id="standard_baselines_v1",
            split_contract_id="breast_visium_split_v1",
            target_definition_id="breast_visium_hallmarks_v1",
            scoring_contract_id="singscore_r_v1",
            manifest_id="breast_manifest_v1",
            source_score_artifact_path="scores.parquet",
            source_score_artifact_hash="a" * 64,
            source_manifest_path="manifest.parquet",
            source_manifest_hash="b" * 64,
            ridge_probe_selected_alpha_by_program=None,
            n_rows=1,
            rows=(
                BaselinePredictionRow(
                    observation_id="obs-1",
                    sample_id="sample-1",
                    cohort_id="cohort-a",
                    split="val",
                    program_name="HALLMARK_HYPOXIA",
                    baseline_name=BaselineName.RIDGE_PROBE,
                    predicted_score=0.42,
                ),
            ),
        )


def test_baseline_prediction_artifact_rejects_non_ridge_rows_with_alpha_metadata(
) -> None:
    with pytest.raises(ValidationError, match="ridge_probe_selected_alpha_by_program"):
        BaselinePredictionArtifact(
            run_id="baseline-run-1",
            baseline_contract_id="standard_baselines_v1",
            split_contract_id="breast_visium_split_v1",
            target_definition_id="breast_visium_hallmarks_v1",
            scoring_contract_id="singscore_r_v1",
            manifest_id="breast_manifest_v1",
            source_score_artifact_path="scores.parquet",
            source_score_artifact_hash="a" * 64,
            source_manifest_path="manifest.parquet",
            source_manifest_hash="b" * 64,
            ridge_probe_selected_alpha_by_program={"HALLMARK_HYPOXIA": 0.1},
            n_rows=1,
            rows=(
                BaselinePredictionRow(
                    observation_id="obs-1",
                    sample_id="sample-1",
                    cohort_id="cohort-a",
                    split="val",
                    program_name="HALLMARK_HYPOXIA",
                    baseline_name=BaselineName.GLOBAL_TRAIN_MEAN,
                    predicted_score=0.42,
                ),
            ),
        )
