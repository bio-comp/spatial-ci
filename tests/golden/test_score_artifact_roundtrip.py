from pathlib import Path

from spatial_ci.scoring.artifacts import (
    ScoreArtifact,
    ScoreFailureCode,
    ScorePacket,
    ScoreStatus,
    SignatureDirection,
    read_score_artifact,
    write_score_artifact,
)


def test_score_artifact_roundtrip_preserves_status_and_provenance(
    tmp_path: Path,
) -> None:
    artifact = ScoreArtifact(
        target_definition_id="breast_visium_hallmarks_v1",
        scoring_contract_id="singscore_r_v1",
        signature_direction=SignatureDirection.UP_ONLY,
        bridge_contract_version="v1",
        generated_at="2026-03-10T00:00:00Z",
        run_id="run-1",
        r_version="4.5.2",
        singscore_version="1.30.0",
        renv_lock_hash="abc123",
        scoring_script_path="scripts/score_targets.R",
        scoring_script_hash="def456",
        source_expression_artifact_hash="expr789",
        source_manifest_id="manifest-1",
        packets=(
            ScorePacket(
                observation_id="obs-1",
                sample_id="sample-1",
                slide_id="slide-1",
                program_name="HALLMARK_HYPOXIA",
                status=ScoreStatus.OK,
                raw_rank_evidence=0.25,
                signature_size_declared=2,
                signature_size_matched=2,
                signature_coverage=1.0,
                dropped_by_missingness_rule=False,
                failure_code=None,
                null_calibrated_score=None,
                dropout_penalty=None,
                spatial_consistency=None,
            ),
            ScorePacket(
                observation_id="obs-2",
                sample_id="sample-1",
                slide_id="slide-1",
                program_name="HALLMARK_HYPOXIA",
                status=ScoreStatus.DROPPED,
                raw_rank_evidence=None,
                signature_size_declared=2,
                signature_size_matched=0,
                signature_coverage=0.0,
                dropped_by_missingness_rule=True,
                failure_code=ScoreFailureCode.EMPTY_SIGNATURE_MATCH,
                null_calibrated_score=None,
                dropout_penalty=None,
                spatial_consistency=None,
            ),
        ),
    )
    output_path = tmp_path / "score_output.parquet"

    write_score_artifact(artifact, output_path)
    reloaded = read_score_artifact(output_path)

    assert reloaded == artifact
