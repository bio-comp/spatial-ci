from pydantic import ValidationError

from spatial_ci.scoring.artifacts import (
    ScoreArtifact,
    ScorePacket,
    ScoreStatus,
    SignatureDirection,
)


def test_score_packet_requires_observation_grain() -> None:
    packet = ScorePacket(
        observation_id="obs-1",
        sample_id="sample-1",
        slide_id="slide-1",
        program_name="HALLMARK_HYPOXIA",
        status=ScoreStatus.OK,
        raw_rank_evidence=0.25,
        signature_size_declared=4,
        signature_size_matched=4,
        signature_coverage=1.0,
        dropped_by_missingness_rule=False,
        failure_code=None,
        null_calibrated_score=None,
        dropout_penalty=None,
        spatial_consistency=None,
    )

    assert packet.observation_id == "obs-1"


def test_score_artifact_keeps_provenance_off_rows() -> None:
    artifact = ScoreArtifact(
        target_definition_id="breast_visium_hallmarks_v1",
        scoring_contract_id="singscore_r_v1",
        signature_direction=SignatureDirection.UP_ONLY,
        bridge_contract_version="v1",
        generated_at="2026-03-10T00:00:00Z",
        run_id="run-1",
        r_version="4.4.0",
        singscore_version="1.30.0",
        renv_lock_hash="abc123",
        scoring_script_path="scripts/score_targets.R",
        scoring_script_hash="def456",
        source_expression_artifact_hash=None,
        source_manifest_id=None,
        packets=(),
    )

    assert artifact.bridge_contract_version == "v1"
    assert artifact.packets == ()


def test_score_packet_rejects_invalid_coverage_fraction() -> None:
    try:
        ScorePacket(
            observation_id="obs-1",
            sample_id=None,
            slide_id=None,
            program_name="HALLMARK_HYPOXIA",
            status=ScoreStatus.OK,
            raw_rank_evidence=0.25,
            signature_size_declared=4,
            signature_size_matched=2,
            signature_coverage=0.1,
            dropped_by_missingness_rule=False,
            failure_code=None,
            null_calibrated_score=None,
            dropout_penalty=None,
            spatial_consistency=None,
        )
    except ValidationError as exc:
        assert "signature_coverage" in str(exc)
    else:
        raise AssertionError("Expected coverage validation to fail.")


def test_score_packet_rejects_ok_status_without_raw_rank_evidence() -> None:
    try:
        ScorePacket(
            observation_id="obs-1",
            sample_id=None,
            slide_id=None,
            program_name="HALLMARK_HYPOXIA",
            status=ScoreStatus.OK,
            raw_rank_evidence=None,
            signature_size_declared=4,
            signature_size_matched=4,
            signature_coverage=1.0,
            dropped_by_missingness_rule=False,
            failure_code=None,
            null_calibrated_score=None,
            dropout_penalty=None,
            spatial_consistency=None,
        )
    except ValidationError as exc:
        assert "raw_rank_evidence" in str(exc)
    else:
        raise AssertionError("Expected ok-status packet validation to fail.")


def test_score_packet_rejects_non_ok_status_without_failure_code() -> None:
    try:
        ScorePacket(
            observation_id="obs-1",
            sample_id=None,
            slide_id=None,
            program_name="HALLMARK_HYPOXIA",
            status=ScoreStatus.DROPPED,
            raw_rank_evidence=None,
            signature_size_declared=4,
            signature_size_matched=0,
            signature_coverage=0.0,
            dropped_by_missingness_rule=True,
            failure_code=None,
            null_calibrated_score=None,
            dropout_penalty=None,
            spatial_consistency=None,
        )
    except ValidationError as exc:
        assert "failure_code" in str(exc)
    else:
        raise AssertionError("Expected non-ok packet validation to fail.")


def test_score_packet_rejects_mismatched_matched_gene_ids() -> None:
    try:
        ScorePacket(
            observation_id="obs-1",
            sample_id=None,
            slide_id=None,
            program_name="HALLMARK_HYPOXIA",
            status=ScoreStatus.OK,
            raw_rank_evidence=0.25,
            signature_size_declared=4,
            signature_size_matched=2,
            signature_coverage=0.5,
            dropped_by_missingness_rule=False,
            failure_code=None,
            null_calibrated_score=None,
            dropout_penalty=None,
            spatial_consistency=None,
            matched_gene_ids=("CA9",),
        )
    except ValidationError as exc:
        assert "matched_gene_ids" in str(exc)
    else:
        raise AssertionError("Expected matched_gene_ids validation to fail.")
