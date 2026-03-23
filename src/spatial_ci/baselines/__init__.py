"""Baseline execution package for Spatial-CI."""

from spatial_ci.baselines.artifacts import (
    BaselineName,
    BaselinePredictionArtifact,
    BaselinePredictionRow,
    read_baseline_prediction_artifact,
    write_baseline_prediction_artifact,
)
from spatial_ci.baselines.knn import predict_knn_on_embeddings
from spatial_ci.baselines.ridge import predict_ridge_probe
from spatial_ci.baselines.runner import run_mean_baselines

__all__ = [
    "BaselineName",
    "BaselinePredictionArtifact",
    "BaselinePredictionRow",
    "read_baseline_prediction_artifact",
    "predict_knn_on_embeddings",
    "predict_ridge_probe",
    "run_mean_baselines",
    "write_baseline_prediction_artifact",
]
