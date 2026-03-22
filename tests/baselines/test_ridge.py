import polars as pl
import pytest

from spatial_ci.baselines.artifacts import BaselineName
from spatial_ci.baselines.ridge import predict_ridge_probe


def _ridge_input_frame() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "observation_id": "train-1",
                "sample_id": "s1",
                "cohort_id": "cohort-a",
                "split": "train",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.0,
                "embedding": [0.0],
            },
            {
                "observation_id": "train-2",
                "sample_id": "s2",
                "cohort_id": "cohort-a",
                "split": "train",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 1.0,
                "embedding": [1.0],
            },
            {
                "observation_id": "val-1",
                "sample_id": "s3",
                "cohort_id": "cohort-a",
                "split": "val",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.2,
                "embedding": [0.2],
            },
            {
                "observation_id": "val-2",
                "sample_id": "s4",
                "cohort_id": "cohort-a",
                "split": "val",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.8,
                "embedding": [0.8],
            },
            {
                "observation_id": "test-1",
                "sample_id": "s5",
                "cohort_id": "external-b",
                "split": "test_external",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.5,
                "embedding": [0.5],
            },
        ]
    )


def test_predict_ridge_probe_selects_alpha_from_frozen_grid() -> None:
    predictions, selected_alpha_by_program = predict_ridge_probe(_ridge_input_frame())

    assert selected_alpha_by_program == {"PROGRAM_A": 0.1}
    assert set(predictions.get_column("baseline_name")) == {
        BaselineName.RIDGE_PROBE.value
    }
    assert predictions.height == 5


def test_predict_ridge_probe_uses_train_only_standardization() -> None:
    frame = pl.DataFrame(
        [
            {
                "observation_id": "train-1",
                "sample_id": "s1",
                "cohort_id": "cohort-a",
                "split": "train",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.0,
                "embedding": [0.0],
            },
            {
                "observation_id": "train-2",
                "sample_id": "s2",
                "cohort_id": "cohort-a",
                "split": "train",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 1.0,
                "embedding": [1.0],
            },
            {
                "observation_id": "val-1",
                "sample_id": "s3",
                "cohort_id": "cohort-a",
                "split": "val",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.5,
                "embedding": [100.0],
            },
        ]
    )

    predictions, _ = predict_ridge_probe(frame, alphas=(0.1,))

    observed = predictions.filter(pl.col("observation_id") == "val-1").item(
        0, "predicted_score"
    )
    assert observed > 50.0


def test_predict_ridge_probe_rejects_program_with_too_few_train_rows() -> None:
    frame = pl.DataFrame(
        [
            {
                "observation_id": "train-1",
                "sample_id": "s1",
                "cohort_id": "cohort-a",
                "split": "train",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.0,
                "embedding": [0.0],
            },
            {
                "observation_id": "val-1",
                "sample_id": "s2",
                "cohort_id": "cohort-a",
                "split": "val",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.5,
                "embedding": [0.5],
            },
        ]
    )

    with pytest.raises(ValueError, match="fewer than 2 train rows"):
        predict_ridge_probe(frame)


def test_predict_ridge_probe_rejects_program_without_val_rows() -> None:
    frame = pl.DataFrame(
        [
            {
                "observation_id": "train-1",
                "sample_id": "s1",
                "cohort_id": "cohort-a",
                "split": "train",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.0,
                "embedding": [0.0],
            },
            {
                "observation_id": "train-2",
                "sample_id": "s2",
                "cohort_id": "cohort-a",
                "split": "train",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 1.0,
                "embedding": [1.0],
            },
        ]
    )

    with pytest.raises(ValueError, match="no val rows"):
        predict_ridge_probe(frame)


def test_predict_ridge_probe_breaks_alpha_ties_toward_smaller_value() -> None:
    frame = pl.DataFrame(
        [
            {
                "observation_id": "train-1",
                "sample_id": "s1",
                "cohort_id": "cohort-a",
                "split": "train",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.5,
                "embedding": [0.0],
            },
            {
                "observation_id": "train-2",
                "sample_id": "s2",
                "cohort_id": "cohort-a",
                "split": "train",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.5,
                "embedding": [1.0],
            },
            {
                "observation_id": "val-1",
                "sample_id": "s3",
                "cohort_id": "cohort-a",
                "split": "val",
                "program_name": "PROGRAM_A",
                "raw_rank_evidence": 0.5,
                "embedding": [0.2],
            },
        ]
    )

    _, selected_alpha_by_program = predict_ridge_probe(frame)

    assert selected_alpha_by_program == {"PROGRAM_A": 0.1}
