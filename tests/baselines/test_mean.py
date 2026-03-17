import polars as pl
import pytest

from spatial_ci.baselines.artifacts import BaselineName
from spatial_ci.baselines.mean import (
    predict_global_train_mean,
    predict_mean_by_train_cohort,
)


def _baseline_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "observation_id": ["obs-1", "obs-2", "obs-3", "obs-4", "obs-5", "obs-6"],
            "sample_id": ["s1", "s2", "s3", "s4", "s5", "s6"],
            "cohort_id": [
                "cohort-a",
                "cohort-a",
                "cohort-a",
                "cohort-a",
                "external-b",
                "cohort-a",
            ],
            "split": ["train", "train", "val", "train", "test_external", "val"],
            "program_name": [
                "HALLMARK_HYPOXIA",
                "HALLMARK_HYPOXIA",
                "HALLMARK_HYPOXIA",
                "HALLMARK_HYPOXIA",
                "HALLMARK_HYPOXIA",
                "HALLMARK_HYPOXIA",
            ],
            "status": ["ok", "ok", "ok", "dropped", "ok", "failed"],
            "raw_rank_evidence": [0.2, 0.6, 0.0, 0.9, 0.0, 0.1],
        }
    )


def test_predict_global_train_mean_uses_train_rows_only() -> None:
    predictions = predict_global_train_mean(_baseline_frame())

    assert (
        predictions.filter(pl.col("observation_id") == "obs-3")
        .item(0, "predicted_score")
        == pytest.approx(0.4)
    )
    assert set(predictions.get_column("baseline_name").to_list()) == {
        BaselineName.GLOBAL_TRAIN_MEAN.value
    }


def test_predict_mean_by_train_cohort_uses_matching_train_cohort_mean() -> None:
    predictions = predict_mean_by_train_cohort(_baseline_frame())

    assert (
        predictions.filter(pl.col("observation_id") == "obs-3")
        .item(0, "predicted_score")
        == pytest.approx(0.4)
    )


def test_predict_mean_by_train_cohort_falls_back_to_global_mean() -> None:
    predictions = predict_mean_by_train_cohort(_baseline_frame())

    assert (
        predictions.filter(pl.col("observation_id") == "obs-5")
        .item(0, "predicted_score")
        == pytest.approx(0.4)
    )


def test_mean_baselines_exclude_dropped_and_failed_rows() -> None:
    global_predictions = predict_global_train_mean(_baseline_frame())
    cohort_predictions = predict_mean_by_train_cohort(_baseline_frame())

    assert set(global_predictions.get_column("observation_id").to_list()) == {
        "obs-1",
        "obs-2",
        "obs-3",
        "obs-5",
    }
    assert set(cohort_predictions.get_column("observation_id").to_list()) == {
        "obs-1",
        "obs-2",
        "obs-3",
        "obs-5",
    }
