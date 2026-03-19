import importlib.util
from pathlib import Path

import polars as pl
from click import Command
from click.testing import CliRunner

from spatial_ci.baselines.artifacts import (
    BaselineName,
    read_baseline_prediction_artifact,
)
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


def _load_run_baselines_main() -> Command:
    module_path = Path("scripts/run_baselines.py").resolve()
    spec = importlib.util.spec_from_file_location("run_baselines_cli", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load scripts/run_baselines.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def _write_inputs(score_path: Path, manifest_path: Path) -> None:
    write_score_artifact(
        ScoreArtifact(
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
            packets=(
                ScorePacket(
                    observation_id="obs-1",
                    sample_id="s1",
                    program_name="HALLMARK_HYPOXIA",
                    status=ScoreStatus.OK,
                    raw_rank_evidence=0.2,
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
                    raw_rank_evidence=0.6,
                    signature_size_declared=10,
                    signature_size_matched=10,
                    signature_coverage=1.0,
                    dropped_by_missingness_rule=False,
                ),
                ScorePacket(
                    observation_id="obs-3",
                    sample_id="s3",
                    program_name="HALLMARK_HYPOXIA",
                    status=ScoreStatus.OK,
                    raw_rank_evidence=0.0,
                    signature_size_declared=10,
                    signature_size_matched=10,
                    signature_coverage=1.0,
                    dropped_by_missingness_rule=False,
                ),
            ),
        ),
        score_path,
    )
    pl.DataFrame(
        [
            {"sample_id": "s1", "cohort_id": "cohort-a", "split": "train"},
            {"sample_id": "s2", "cohort_id": "cohort-a", "split": "train"},
            {"sample_id": "s3", "cohort_id": "external-b", "split": "test_external"},
        ]
    ).write_parquet(manifest_path)


def _write_embedding_inputs(embedding_path: Path) -> None:
    write_embedding_artifact(
        EmbeddingArtifact(
            alignment_contract_id="alignment-v1",
            encoder_name="test-encoder",
            encoder_version="1.0.0",
            source_image_artifact_path="images.parquet",
            source_image_artifact_hash="d" * 64,
            n_rows=3,
            rows=(
                EmbeddingArtifactRow(
                    observation_id="obs-1",
                    sample_id="s1",
                    embedding=(0.1, 0.2),
                ),
                EmbeddingArtifactRow(
                    observation_id="obs-2",
                    sample_id="s2",
                    embedding=(0.2, 0.3),
                ),
                EmbeddingArtifactRow(
                    observation_id="obs-3",
                    sample_id="s3",
                    embedding=(0.3, 0.4),
                ),
            ),
        ),
        embedding_path,
    )


def test_run_baselines_cli_writes_prediction_artifact(tmp_path: Path) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    _write_inputs(score_path, manifest_path)

    runner = CliRunner()
    main = _load_run_baselines_main()
    result = runner.invoke(
        main,
        [
            "--scores",
            str(score_path),
            "--manifest",
            str(manifest_path),
            "--output",
            str(output_path),
            "--run-id",
            "baseline-run-1",
            "--baseline-contract-id",
            "mean_baselines_v0",
            "--split-contract-id",
            "breast_visium_split_v1",
            "--manifest-id",
            "manifest-v1",
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    artifact = read_baseline_prediction_artifact(output_path)
    assert artifact.n_rows == 6


def test_run_baselines_cli_writes_mean_and_knn_predictions_with_embeddings(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    embedding_path = tmp_path / "embeddings.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    _write_inputs(score_path, manifest_path)
    _write_embedding_inputs(embedding_path)

    runner = CliRunner()
    main = _load_run_baselines_main()
    result = runner.invoke(
        main,
        [
            "--scores",
            str(score_path),
            "--manifest",
            str(manifest_path),
            "--output",
            str(output_path),
            "--run-id",
            "baseline-run-1",
            "--baseline-contract-id",
            "mean_baselines_v0",
            "--split-contract-id",
            "breast_visium_split_v1",
            "--manifest-id",
            "manifest-v1",
            "--embeddings",
            str(embedding_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    artifact = read_baseline_prediction_artifact(output_path)
    assert artifact.n_rows == 9
    assert {row.baseline_name for row in artifact.rows} == {
        BaselineName.GLOBAL_TRAIN_MEAN,
        BaselineName.MEAN_BY_TRAIN_COHORT,
        BaselineName.KNN_ON_EMBEDDINGS,
    }


def test_run_baselines_cli_fails_cleanly_for_missing_embeddings(
    tmp_path: Path,
) -> None:
    score_path = tmp_path / "scores.parquet"
    manifest_path = tmp_path / "manifest.parquet"
    output_path = tmp_path / "baseline_predictions.parquet"
    embedding_path = tmp_path / "missing-embeddings.parquet"
    _write_inputs(score_path, manifest_path)

    runner = CliRunner()
    main = _load_run_baselines_main()
    result = runner.invoke(
        main,
        [
            "--scores",
            str(score_path),
            "--manifest",
            str(manifest_path),
            "--output",
            str(output_path),
            "--run-id",
            "baseline-run-1",
            "--baseline-contract-id",
            "mean_baselines_v0",
            "--split-contract-id",
            "breast_visium_split_v1",
            "--manifest-id",
            "manifest-v1",
            "--embeddings",
            str(embedding_path),
        ],
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, FileNotFoundError)


def test_run_baselines_cli_requires_explicit_arguments() -> None:
    runner = CliRunner()
    main = _load_run_baselines_main()
    result = runner.invoke(main, [])

    assert result.exit_code != 0
    assert "--scores" in result.output
