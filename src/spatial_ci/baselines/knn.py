"""Frozen KNN baseline predictions on embedding vectors."""

from __future__ import annotations

from collections.abc import Sequence
from math import isfinite
from typing import TypedDict, cast

import numpy as np
import polars as pl

from spatial_ci.baselines.artifacts import BaselineName

REQUIRED_COLUMNS = {
    "observation_id",
    "sample_id",
    "cohort_id",
    "split",
    "program_name",
    "raw_rank_evidence",
    "embedding",
}


class _KnnRow(TypedDict):
    observation_id: str
    sample_id: str
    cohort_id: str
    split: str
    program_name: str
    raw_rank_evidence: float
    embedding: Sequence[float]


def _validate_required_columns(frame: pl.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        missing_display = ", ".join(missing)
        raise ValueError(f"baseline input frame is missing columns: {missing_display}")


def _cosine_distance(left: Sequence[float], right: Sequence[float]) -> float:
    left_array = np.asarray(left, dtype=float)
    right_array = np.asarray(right, dtype=float)
    left_norm = float(np.linalg.norm(left_array))
    right_norm = float(np.linalg.norm(right_array))
    if left_norm == 0.0 or right_norm == 0.0:
        raise ValueError("embedding vectors must be non-zero for cosine distance")
    similarity = float(np.dot(left_array, right_array) / (left_norm * right_norm))
    if not isfinite(similarity):
        raise ValueError("embedding vectors produced a non-finite cosine similarity")
    return 1.0 - similarity


def _candidate_rows_for_program(
    frame: pl.DataFrame, program_name: str
) -> list[_KnnRow]:
    program_rows = frame.filter(pl.col("program_name") == program_name)
    train_rows = program_rows.filter(pl.col("split") == "train")
    if train_rows.height == 0:
        raise ValueError(f"program {program_name} has no train rows")
    return cast("list[_KnnRow]", train_rows.to_dicts())


def _predict_row(
    row: _KnnRow,
    candidates: list[_KnnRow],
    *,
    k: int,
) -> float:
    query_embedding = row["embedding"]
    query_observation_id = row["observation_id"]

    neighbor_distances: list[tuple[float, str, float]] = []
    for candidate in candidates:
        if row["split"] == "train" and candidate["observation_id"] == (
            query_observation_id
        ):
            continue
        distance = _cosine_distance(query_embedding, candidate["embedding"])
        neighbor_distances.append(
            (
                distance,
                candidate["observation_id"],
                float(candidate["raw_rank_evidence"]),
            )
        )

    if not neighbor_distances:
        raise ValueError(
            "program "
            f"{row['program_name']} has no train neighbors for observation "
            f"{query_observation_id}"
        )

    neighbor_distances.sort(key=lambda item: (item[0], item[1]))
    selected_neighbors = neighbor_distances[: min(k, len(neighbor_distances))]
    return float(
        sum(score for _, _, score in selected_neighbors) / len(selected_neighbors)
    )


def predict_knn_on_embeddings(frame: pl.DataFrame, *, k: int = 20) -> pl.DataFrame:
    """Predict raw rank evidence by averaging nearest train embeddings."""

    _validate_required_columns(frame)
    if k < 1:
        raise ValueError("k must be at least 1")

    program_names = sorted(frame.get_column("program_name").unique())
    candidates_by_program = {
        program_name: _candidate_rows_for_program(frame, program_name)
        for program_name in program_names
    }

    predictions: list[dict[str, object]] = []
    for row in cast("list[_KnnRow]", frame.to_dicts()):
        program_name = row["program_name"]
        predicted_score = _predict_row(
            row,
            candidates_by_program[program_name],
            k=k,
        )
        predictions.append(
            {
                "observation_id": row["observation_id"],
                "sample_id": row["sample_id"],
                "cohort_id": row["cohort_id"],
                "split": row["split"],
                "program_name": program_name,
                "baseline_name": BaselineName.KNN_ON_EMBEDDINGS.value,
                "predicted_score": predicted_score,
            }
        )

    return pl.DataFrame(predictions)


__all__ = ["predict_knn_on_embeddings"]
