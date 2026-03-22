"""Frozen ridge baseline predictions on embedding vectors."""

from __future__ import annotations

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

DEFAULT_ALPHAS = (0.1, 1.0, 10.0)


class _RidgeRow(TypedDict):
    observation_id: str
    sample_id: str
    cohort_id: str
    split: str
    program_name: str
    raw_rank_evidence: float
    embedding: list[float]


def _validate_required_columns(frame: pl.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        missing_display = ", ".join(missing)
        raise ValueError(f"baseline input frame is missing columns: {missing_display}")


def _validated_alphas(alphas: tuple[float, ...]) -> tuple[float, ...]:
    if not alphas:
        raise ValueError("alphas must not be empty")
    invalid = [alpha for alpha in alphas if not isfinite(alpha) or alpha <= 0.0]
    if invalid:
        raise ValueError("alphas must be positive finite values")
    return tuple(sorted(alphas))


def _embedding_matrix(rows: list[_RidgeRow], *, program_name: str) -> np.ndarray:
    embeddings = np.asarray([row["embedding"] for row in rows], dtype=float)
    if embeddings.ndim != 2:
        raise ValueError(f"program {program_name} has malformed embedding rows")
    if embeddings.shape[1] == 0:
        raise ValueError(f"program {program_name} has empty embedding vectors")
    if not np.isfinite(embeddings).all():
        raise ValueError(f"program {program_name} has non-finite embedding values")
    return embeddings


def _response_vector(rows: list[_RidgeRow]) -> np.ndarray:
    return np.asarray([row["raw_rank_evidence"] for row in rows], dtype=float)


def _standardize(
    train_matrix: np.ndarray, matrix: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    means = train_matrix.mean(axis=0)
    scales = train_matrix.std(axis=0)
    scales[scales == 0.0] = 1.0
    return (train_matrix - means) / scales, (matrix - means) / scales, means


def _ridge_coefficients(
    standardized_train: np.ndarray, responses: np.ndarray, *, alpha: float
) -> np.ndarray:
    design = np.column_stack([np.ones(standardized_train.shape[0]), standardized_train])
    penalty = np.eye(design.shape[1], dtype=float)
    penalty[0, 0] = 0.0
    system = design.T @ design + (alpha * penalty)
    rhs = design.T @ responses
    try:
        return np.linalg.solve(system, rhs)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(system) @ rhs


def _ridge_predict(standardized: np.ndarray, coefficients: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(standardized.shape[0]), standardized])
    return design @ coefficients


def _program_predictions(
    program_frame: pl.DataFrame, *, alphas: tuple[float, ...]
) -> tuple[list[dict[str, object]], float]:
    program_rows = cast("list[_RidgeRow]", program_frame.to_dicts())
    if not program_rows:
        raise ValueError("program frame must not be empty")
    program_name = program_rows[0]["program_name"]

    train_rows = [row for row in program_rows if row["split"] == "train"]
    val_rows = [row for row in program_rows if row["split"] == "val"]
    if len(train_rows) < 2:
        raise ValueError(f"program {program_name} has fewer than 2 train rows")
    if not val_rows:
        raise ValueError(f"program {program_name} has no val rows")

    train_matrix = _embedding_matrix(train_rows, program_name=program_name)
    all_matrix = _embedding_matrix(program_rows, program_name=program_name)
    standardized_train, standardized_all, _ = _standardize(train_matrix, all_matrix)
    train_response = _response_vector(train_rows)

    val_index_by_observation_id = {
        row["observation_id"]: index for index, row in enumerate(program_rows)
    }
    val_indices = [
        val_index_by_observation_id[row["observation_id"]] for row in val_rows
    ]
    standardized_val = standardized_all[val_indices]
    val_response = _response_vector(val_rows)

    best_alpha: float | None = None
    best_score: float | None = None
    best_coefficients: np.ndarray | None = None
    for alpha in alphas:
        coefficients = _ridge_coefficients(
            standardized_train,
            train_response,
            alpha=alpha,
        )
        val_predictions = _ridge_predict(standardized_val, coefficients)
        mse = float(np.mean(np.square(val_predictions - val_response)))
        if best_score is None or mse < best_score or (
            np.isclose(mse, best_score)
            and best_alpha is not None
            and alpha < best_alpha
        ):
            best_alpha = alpha
            best_score = mse
            best_coefficients = coefficients

    if best_alpha is None or best_coefficients is None:
        raise ValueError(f"program {program_name} did not produce a valid ridge fit")

    all_predictions = _ridge_predict(standardized_all, best_coefficients)
    predictions = [
        {
            "observation_id": row["observation_id"],
            "sample_id": row["sample_id"],
            "cohort_id": row["cohort_id"],
            "split": row["split"],
            "program_name": program_name,
            "baseline_name": BaselineName.RIDGE_PROBE.value,
            "predicted_score": float(predicted_score),
        }
        for row, predicted_score in zip(program_rows, all_predictions, strict=True)
    ]
    return predictions, best_alpha


def predict_ridge_probe(
    frame: pl.DataFrame, *, alphas: tuple[float, ...] = DEFAULT_ALPHAS
) -> tuple[pl.DataFrame, dict[str, float]]:
    """Predict raw rank evidence with frozen ridge semantics."""

    _validate_required_columns(frame)
    validated_alphas = _validated_alphas(alphas)

    predictions: list[dict[str, object]] = []
    selected_alpha_by_program: dict[str, float] = {}
    for program_name in sorted(frame.get_column("program_name").unique()):
        program_frame = frame.filter(pl.col("program_name") == program_name)
        program_predictions, best_alpha = _program_predictions(
            program_frame,
            alphas=validated_alphas,
        )
        predictions.extend(program_predictions)
        selected_alpha_by_program[str(program_name)] = best_alpha

    return pl.DataFrame(predictions), selected_alpha_by_program


__all__ = ["predict_ridge_probe"]
