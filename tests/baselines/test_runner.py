from pathlib import Path

import polars as pl
import pytest

from spatial_ci.baselines.artifacts import (
    BaselineName,
    read_baseline_prediction_artifact,
)
from spatial_ci.baselines.runner import run_mean_baselines
from spatial_ci.embeddings.artifacts import (
    EmbeddingArtifact,
    EmbeddingArtifactRow,
    write_embedding_artifact,
)
from spatial_ci.scoring.artifacts import (
    ScoreArtifact,
    ScorePacket,
    ScoreStatus,
    SignatureDirection,
    write_score_artifact,
)


def _score_artifact(
    *, sample_id_obs3: str | None = "s3", include_missing_manifest_row: bool = False
) -> ScoreArtifact:
    packets = (
        ScorePacket(
            observation_id="obs-1",
            sample_id="s1",
            program_name="HALLMARK_HYPOXIA",
            status=ScoreStatus.OK,
            raw_rank_evidence=0.0,
            signature_size_declared=10,
            signature_size_matched=10,
            signature_coverage=1.0,
            dropped_by_missingness_rule=False,
        ),
        ScorePacket(
            observation_id="obs-2",
            sample_id="s2",
            program_name="HALLMARK_HYPOXIA",
            status=ScoreStatus.OK,
            raw_rank_evidence=1.0,
            signature_size_declared=10,
            signature_size_matched=10,
            signature_coverage=1.0,
            dropped_by_missingness_rule=False,
        ),
        ScorePacket(
            observation_id="obs-3",
            sample_id=sample_id_obs3,
            program_name="HALLMARK_HYPOXIA",
            status=ScoreStatus.OK,
            raw_rank_evidence=0.2,
            signature_size_declared=10,
            signature_size_matched=10,
            signature_coverage=1.0,
            dropped_by_missingness_rule=False,
        ),
        ScorePacket(
            observation_id="obs-4",
            sample_id="s5" if include_missing_manifest_row else "s4",
            program_name="HALLMARK_HYPOXIA",
            status=ScoreStatus.OK,
            raw_rank_evidence=0.5,
            signature_size_declared=10,
            signature_size_matched=10,
            signature_coverage=1.0,
            dropped_by_missingness_rule=False,
        ),
    )
    return ScoreArtifact(
        target_definition_id="breast_visium_hallmarks_v1",
        scoring_contract_id="singscore_r_v1",
        signature_direction=SignatureDirection.UP_ONLY,
        bridge_contract_version="v1",
        generated_at="2026-03-16T00:00:00Z",
        run_id="score-run-1",
        r_version="4.5.0",
        singscore_version="1.30.0",
        renv_lock_hash="a" * 64,
        scoring_script_path="scripts/score_targets.R",
        scoring_script_hash="b" * 64,
        source_expression_artifact_hash="c" * 64,
        source_manifest_id="manifest-v1",
        packets=packets,
    )


def _write_manifest(
    path: Path,
    *,
    duplicate_sample_id: bool = False,
    split_by_sample: dict[str, str] | None = None,
) -> None:
    if split_by_sample is None:
        split_by_sample = {
            "s1": "train",
            "s2": "train",
            "s3": "val",
            "s4": "test_external",
        }
    rows = [
        {
            "sample_id": sample_id,
            "cohort_id": "external-b" if split == "test_external" else "cohort-a",
            "split": split,
        }
        for sample_id, split in split_by_sample.items()
    ]
    if duplicate_sample_id:
        rows.append(
            {
                "sample_id": "s4",
                "cohort_id": "external-b",
                "split": "test_external",
            }
        )
    pl.DataFrame(rows).write_parquet(path)


def _write_embedding_artifact(
    path: Path,
    *,
    include_obs4: bool = True,
    duplicate_observation_id: bool = False,
    inconsistent_dimensions: bool = False,
) -> None:
    rows = [
        EmbeddingArtifactRow.model_construct(
            observation_id="obs-1",
            sample_id="s1",
            embedding=(1.0,),
        ),
        EmbeddingArtifactRow.model_construct(
            observation_id="obs-2",
            sample_id="s2",
            embedding=(2.0, 3.0) if inconsistent_dimensions else (2.0,),
        ),
        EmbeddingArtifactRow.model_construct(
            observation_id="obs-3",
            sample_id="s3",
            embedding=(1.2,),
        ),
    ]
    if include_obs4:
        rows.append(
            EmbeddingArtifactRow.model_construct(
                observation_id="obs-4",
                sample_id="s4",
                embedding=(1.5,),
            )
        )
    if duplicate_observation_id:
        rows[-1] = EmbeddingArtifactRow.model_construct(
            observation_id="obs-3",
            sample_id="s3",
            embedding=(1.5,),
        )
    artifact = EmbeddingArtifact.model_construct(
        alignment_contract_id="alignment-v1",
        encoder_name="encoder-x",
        encoder_version="1.0.0",
        source_image_artifact_path="images.parquet",
        source_image_artifact_hash="d" * 64,
        n_rows=len(rows),
        rows=tuple(rows),
    )
    write_embedding_artifact(artifact, path)


def test_run_mean_baselines_writes_long_form_predictions(tmp_path: Path) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(), score_path)
    _write_manifest(manifest_path)

    artifact = run_mean_baselines(
        score_artifact_path=score_path,
        manifest_path=manifest_path,
        output_path=output_path,
        run_id="baseline-run-1",
        baseline_contract_id="mean_baselines_v0",
        split_contract_id="breast_visium_split_v1",
        manifest_id="manifest-v1",
    )

    observed = read_baseline_prediction_artifact(output_path)
    assert output_path.exists()
    assert artifact == observed
    assert artifact.n_rows == 8
    assert {row.baseline_name for row in artifact.rows} == {
        BaselineName.GLOBAL_TRAIN_MEAN,
        BaselineName.MEAN_BY_TRAIN_COHORT,
    }


def test_run_mean_baselines_writes_mean_and_knn_predictions_with_embeddings(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    embedding_path = tmp_path / "embeddings.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(), score_path)
    _write_manifest(manifest_path)
    _write_embedding_artifact(embedding_path)

    artifact = run_mean_baselines(
        score_artifact_path=score_path,
        manifest_path=manifest_path,
        output_path=output_path,
        run_id="baseline-run-1",
        baseline_contract_id="mean_baselines_v0",
        split_contract_id="breast_visium_split_v1",
        manifest_id="manifest-v1",
        embedding_artifact_path=embedding_path,
    )

    assert output_path.exists()
    assert artifact.n_rows == 16
    assert {row.baseline_name for row in artifact.rows} == {
        BaselineName.GLOBAL_TRAIN_MEAN,
        BaselineName.MEAN_BY_TRAIN_COHORT,
        BaselineName.KNN_ON_EMBEDDINGS,
        BaselineName.RIDGE_PROBE,
    }
    assert artifact.ridge_probe_selected_alpha_by_program == {
        "HALLMARK_HYPOXIA": 0.1
    }
    assert len(
        [
            row
            for row in artifact.rows
            if row.baseline_name is BaselineName.KNN_ON_EMBEDDINGS
        ]
    ) == 4
    assert len(
        [
            row
            for row in artifact.rows
            if row.baseline_name is BaselineName.RIDGE_PROBE
        ]
    ) == 4


def test_run_mean_baselines_rejects_missing_embedding_for_eligible_score_row(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    embedding_path = tmp_path / "embeddings.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(), score_path)
    _write_manifest(manifest_path)
    _write_embedding_artifact(embedding_path, include_obs4=False)

    with pytest.raises(ValueError, match="embedding"):
        run_mean_baselines(
            score_artifact_path=score_path,
            manifest_path=manifest_path,
            output_path=output_path,
            run_id="baseline-run-1",
            baseline_contract_id="mean_baselines_v0",
            split_contract_id="breast_visium_split_v1",
            manifest_id="manifest-v1",
            embedding_artifact_path=embedding_path,
        )


def test_run_mean_baselines_rejects_duplicate_embedding_observation_id(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    embedding_path = tmp_path / "embeddings.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(), score_path)
    _write_manifest(manifest_path)
    _write_embedding_artifact(embedding_path, duplicate_observation_id=True)

    with pytest.raises(ValueError, match="observation_id"):
        run_mean_baselines(
            score_artifact_path=score_path,
            manifest_path=manifest_path,
            output_path=output_path,
            run_id="baseline-run-1",
            baseline_contract_id="mean_baselines_v0",
            split_contract_id="breast_visium_split_v1",
            manifest_id="manifest-v1",
            embedding_artifact_path=embedding_path,
        )


def test_run_mean_baselines_rejects_inconsistent_embedding_dimensionality(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    embedding_path = tmp_path / "embeddings.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(), score_path)
    _write_manifest(manifest_path)
    _write_embedding_artifact(embedding_path, inconsistent_dimensions=True)

    with pytest.raises(ValueError, match="consistent dimensionality"):
        run_mean_baselines(
            score_artifact_path=score_path,
            manifest_path=manifest_path,
            output_path=output_path,
            run_id="baseline-run-1",
            baseline_contract_id="mean_baselines_v0",
            split_contract_id="breast_visium_split_v1",
            manifest_id="manifest-v1",
            embedding_artifact_path=embedding_path,
        )


def test_run_mean_baselines_without_embeddings_preserves_mean_only_behavior(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(), score_path)
    _write_manifest(manifest_path)

    artifact = run_mean_baselines(
        score_artifact_path=score_path,
        manifest_path=manifest_path,
        output_path=output_path,
        run_id="baseline-run-1",
        baseline_contract_id="mean_baselines_v0",
        split_contract_id="breast_visium_split_v1",
        manifest_id="manifest-v1",
    )

    assert artifact.n_rows == 8
    assert artifact.ridge_probe_selected_alpha_by_program is None
    assert {row.baseline_name for row in artifact.rows} == {
        BaselineName.GLOBAL_TRAIN_MEAN,
        BaselineName.MEAN_BY_TRAIN_COHORT,
    }


def test_run_mean_baselines_with_embeddings_rejects_program_without_val_rows(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    embedding_path = tmp_path / "embeddings.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(), score_path)
    _write_manifest(
        manifest_path,
        split_by_sample={
            "s1": "train",
            "s2": "train",
            "s3": "test_external",
            "s4": "test_external",
        },
    )
    _write_embedding_artifact(embedding_path)

    with pytest.raises(ValueError, match="no val rows"):
        run_mean_baselines(
            score_artifact_path=score_path,
            manifest_path=manifest_path,
            output_path=output_path,
            run_id="baseline-run-1",
            baseline_contract_id="mean_baselines_v0",
            split_contract_id="breast_visium_split_v1",
            manifest_id="manifest-v1",
            embedding_artifact_path=embedding_path,
        )


def test_run_mean_baselines_with_embeddings_rejects_program_with_too_few_train_rows(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    embedding_path = tmp_path / "embeddings.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(), score_path)
    _write_manifest(
        manifest_path,
        split_by_sample={
            "s1": "train",
            "s2": "val",
            "s3": "test_external",
            "s4": "test_external",
        },
    )
    _write_embedding_artifact(embedding_path)

    with pytest.raises(ValueError, match="fewer than 2 train rows"):
        run_mean_baselines(
            score_artifact_path=score_path,
            manifest_path=manifest_path,
            output_path=output_path,
            run_id="baseline-run-1",
            baseline_contract_id="mean_baselines_v0",
            split_contract_id="breast_visium_split_v1",
            manifest_id="manifest-v1",
            embedding_artifact_path=embedding_path,
        )


def test_run_mean_baselines_rejects_missing_sample_id_on_ok_score_row(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(sample_id_obs3=None), score_path)
    _write_manifest(manifest_path)

    with pytest.raises(ValueError, match="sample_id"):
        run_mean_baselines(
            score_artifact_path=score_path,
            manifest_path=manifest_path,
            output_path=output_path,
            run_id="baseline-run-1",
            baseline_contract_id="mean_baselines_v0",
            split_contract_id="breast_visium_split_v1",
            manifest_id="manifest-v1",
        )


def test_run_mean_baselines_rejects_duplicate_manifest_sample_id(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(), score_path)
    _write_manifest(manifest_path, duplicate_sample_id=True)

    with pytest.raises(ValueError, match="duplicate sample_id"):
        run_mean_baselines(
            score_artifact_path=score_path,
            manifest_path=manifest_path,
            output_path=output_path,
            run_id="baseline-run-1",
            baseline_contract_id="mean_baselines_v0",
            split_contract_id="breast_visium_split_v1",
            manifest_id="manifest-v1",
        )


def test_run_mean_baselines_rejects_scores_missing_from_manifest(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    write_score_artifact(_score_artifact(include_missing_manifest_row=True), score_path)
    _write_manifest(manifest_path)

    with pytest.raises(ValueError, match="missing from manifest"):
        run_mean_baselines(
            score_artifact_path=score_path,
            manifest_path=manifest_path,
            output_path=output_path,
            run_id="baseline-run-1",
            baseline_contract_id="mean_baselines_v0",
            split_contract_id="breast_visium_split_v1",
            manifest_id="manifest-v1",
        )
