import polars as pl
import pytest

from spatial_ci.baselines.artifacts import BaselineName
from spatial_ci.baselines.knn import predict_knn_on_embeddings


def _knn_frame(*, include_missing_train_program: bool = False) -> pl.DataFrame:
    program_names = [
        "HALLMARK_HYPOXIA",
        "HALLMARK_HYPOXIA",
        "HALLMARK_HYPOXIA",
        "HALLMARK_HYPOXIA",
        "HALLMARK_E2F_TARGETS",
        "HALLMARK_E2F_TARGETS",
        "HALLMARK_E2F_TARGETS",
    ]
    if include_missing_train_program:
        program_names.append("HALLMARK_INTERFERON_GAMMA_RESPONSE")
    else:
        program_names.append("HALLMARK_E2F_TARGETS")

    return pl.DataFrame(
        {
            "observation_id": [
                "train-1",
                "train-2",
                "val-1",
                "test-1",
                "train-a",
                "train-b",
                "train-c",
                "val-b",
            ],
            "sample_id": [
                "sample-1",
                "sample-2",
                "sample-3",
                "sample-4",
                "sample-a",
                "sample-b",
                "sample-c",
                "sample-d",
            ],
            "cohort_id": [
                "cohort-a",
                "cohort-a",
                "cohort-a",
                "cohort-a",
                "cohort-b",
                "cohort-b",
                "cohort-b",
                "cohort-b",
            ],
            "split": [
                "train",
                "train",
                "val",
                "test_external",
                "train",
                "train",
                "train",
                "val",
            ],
            "program_name": program_names,
            "raw_rank_evidence": [
                0.1,
                0.8,
                0.5,
                0.0,
                0.2,
                0.4,
                0.8,
                0.7,
            ],
            "embedding": [
                [1.0, 0.0],
                [0.9, 0.1],
                [1.0, 0.05],
                [1.0, 0.01],
                [1.0, 0.0],
                [0.5, 0.5],
                [0.0, 1.0],
                [0.0, 1.0],
            ],
        }
    )


def test_predict_knn_on_embeddings_uses_train_rows_only() -> None:
    predictions = predict_knn_on_embeddings(_knn_frame(), k=1)

    assert (
        predictions.filter(pl.col("observation_id") == "val-1")
        .item(0, "predicted_score")
        == pytest.approx(0.1)
    )
    assert set(predictions.get_column("baseline_name").to_list()) == {
        BaselineName.KNN_ON_EMBEDDINGS.value
    }


def test_predict_knn_on_embeddings_excludes_self_for_train_rows() -> None:
    predictions = predict_knn_on_embeddings(_knn_frame(), k=1)

    assert (
        predictions.filter(pl.col("observation_id") == "train-1")
        .item(0, "predicted_score")
        == pytest.approx(0.8)
    )


def test_predict_knn_on_embeddings_uses_all_train_neighbors_when_fewer_than_k() -> None:
    predictions = predict_knn_on_embeddings(_knn_frame(), k=20)

    assert (
        predictions.filter(pl.col("observation_id") == "val-b")
        .item(0, "predicted_score")
        == pytest.approx((0.2 + 0.4 + 0.8) / 3)
    )


def test_predict_knn_on_embeddings_rejects_programs_without_train_rows() -> None:
    with pytest.raises(ValueError, match="no train rows"):
        predict_knn_on_embeddings(_knn_frame(include_missing_train_program=True), k=1)
