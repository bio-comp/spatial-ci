"""Baseline runner orchestration for mean-based deployable baselines."""

import hashlib
from pathlib import Path

import polars as pl

from spatial_ci.baselines.artifacts import (
    BaselinePredictionArtifact,
    BaselinePredictionRow,
    write_baseline_prediction_artifact,
)
from spatial_ci.baselines.mean import (
    predict_global_train_mean,
    predict_mean_by_train_cohort,
)
from spatial_ci.scoring.artifacts import read_score_artifact

MANIFEST_REQUIRED_COLUMNS = {"sample_id", "cohort_id", "split"}


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_frame(path: Path) -> pl.DataFrame:
    frame = pl.read_parquet(path)
    missing = sorted(MANIFEST_REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        missing_display = ", ".join(missing)
        raise ValueError(f"manifest is missing required columns: {missing_display}")

    duplicate_rows = frame.filter(pl.col("sample_id").is_duplicated())
    if duplicate_rows.height > 0:
        raise ValueError("manifest contains duplicate sample_id values")

    return frame.select(["sample_id", "cohort_id", "split"])


def _score_frame(path: Path) -> tuple[str, str, str | None, pl.DataFrame]:
    artifact = read_score_artifact(path)
    rows: list[dict[str, object]] = []
    for packet in artifact.packets:
        if packet.status.name.lower() != "ok":
            continue
        if packet.sample_id is None:
            raise ValueError(
                "eligible score rows must carry sample_id for baseline joins"
            )
        rows.append(
            {
                "observation_id": packet.observation_id,
                "sample_id": packet.sample_id,
                "program_name": packet.program_name,
                "status": packet.status.value,
                "raw_rank_evidence": packet.raw_rank_evidence,
            }
        )

    if not rows:
        raise ValueError("score artifact has no eligible score rows")

    return (
        artifact.target_definition_id,
        artifact.scoring_contract_id,
        artifact.source_manifest_id,
        pl.DataFrame(rows),
    )


def _joined_baseline_frame(
    score_frame: pl.DataFrame,
    manifest_frame: pl.DataFrame,
) -> pl.DataFrame:
    missing_samples = sorted(
        set(score_frame.get_column("sample_id").to_list())
        - set(manifest_frame.get_column("sample_id").to_list())
    )
    if missing_samples:
        missing_display = ", ".join(missing_samples)
        raise ValueError(
            "score rows are missing from manifest sample_id coverage: "
            f"{missing_display}"
        )

    return score_frame.join(manifest_frame, on="sample_id", how="left", validate="m:1")


def _prediction_rows(frame: pl.DataFrame) -> tuple[BaselinePredictionRow, ...]:
    ordered = frame.sort(
        by=[
            "split",
            "cohort_id",
            "sample_id",
            "observation_id",
            "program_name",
            "baseline_name",
        ]
    )
    return tuple(
        BaselinePredictionRow.model_validate(row)
        for row in ordered.to_dicts()
    )


def run_mean_baselines(
    *,
    score_artifact_path: Path,
    manifest_path: Path,
    output_path: Path,
    run_id: str,
    baseline_contract_id: str,
    split_contract_id: str,
    manifest_id: str | None,
) -> BaselinePredictionArtifact:
    """Run the mean-based deployable baselines and write the prediction artifact."""

    target_definition_id, scoring_contract_id, source_manifest_id, score_frame = (
        _score_frame(score_artifact_path)
    )
    joined = _joined_baseline_frame(score_frame, _manifest_frame(manifest_path))
    prediction_frame = pl.concat(
        [
            predict_global_train_mean(joined),
            predict_mean_by_train_cohort(joined),
        ],
        how="vertical",
    )
    rows = _prediction_rows(prediction_frame)
    artifact = BaselinePredictionArtifact(
        run_id=run_id,
        baseline_contract_id=baseline_contract_id,
        split_contract_id=split_contract_id,
        target_definition_id=target_definition_id,
        scoring_contract_id=scoring_contract_id,
        manifest_id=manifest_id or source_manifest_id,
        source_score_artifact_path=str(score_artifact_path),
        source_score_artifact_hash=_hash_file(score_artifact_path),
        source_manifest_path=str(manifest_path),
        source_manifest_hash=_hash_file(manifest_path),
        n_rows=len(rows),
        rows=rows,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_baseline_prediction_artifact(artifact, output_path)
    return artifact


__all__ = [
    "run_mean_baselines",
]
