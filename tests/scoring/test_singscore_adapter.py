import importlib
import subprocess

import pyarrow as pa
import pytest

from spatial_ci.scoring import (
    ScoreArtifact,
    ScoreFailureCode,
    ScorePacket,
    ScoreStatus,
    SignatureDirection,
    score_batch,
    score_one,
)
from spatial_ci.signatures import GeneSignature

SINGSCORE_MODULE = importlib.import_module("spatial_ci.scoring.singscore")


def _artifact_with_single_packet(packet: ScorePacket) -> ScoreArtifact:
    return ScoreArtifact(
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
        packets=(packet,),
    )


def test_score_one_delegates_to_score_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_score_batch(**kwargs: object) -> ScoreArtifact:
        calls.append(kwargs)
        return _artifact_with_single_packet(
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
            )
        )

    monkeypatch.setattr(SINGSCORE_MODULE, "score_batch", fake_score_batch)

    packet = score_one(
        observation_id="obs-1",
        expression_by_gene={"CA9": 5.0, "VEGFA": 4.0},
        signature=GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),
        scoring_contract_id="singscore_r_v1",
        target_definition_id="breast_visium_hallmarks_v1",
        sample_id="sample-1",
        slide_id="slide-1",
    )

    assert packet.observation_id == "obs-1"
    assert len(calls) == 1


def test_score_batch_maps_r_output_to_ok_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "run_r_script",
        lambda paths, repo_root: subprocess.CompletedProcess(
            args=["Rscript"], returncode=0, stdout="", stderr=""
        ),
    )
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "load_score_output",
        lambda path: pa.table(
            {
                "observation_id": ["obs-1"],
                "program_name": ["HALLMARK_HYPOXIA"],
                "raw_rank_evidence": [0.25],
                "signature_size_matched": [2],
            }
        ),
    )

    artifact = score_batch(
        expression_matrix={"obs-1": {"CA9": 5.0, "VEGFA": 4.0}},
        signatures=(GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),),
        scoring_contract_id="singscore_r_v1",
        target_definition_id="breast_visium_hallmarks_v1",
        sample_ids_by_observation={"obs-1": "sample-1"},
        slide_ids_by_observation={"obs-1": "slide-1"},
    )

    assert artifact.packets[0].status is ScoreStatus.OK
    assert artifact.packets[0].failure_code is None
    assert artifact.packets[0].sample_id == "sample-1"


def test_score_batch_drops_empty_signature_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "run_r_script",
        lambda paths, repo_root: subprocess.CompletedProcess(
            args=["Rscript"], returncode=0, stdout="", stderr=""
        ),
    )
    monkeypatch.setattr(
        SINGSCORE_MODULE,
        "load_score_output",
        lambda path: pa.table(
            {
                "observation_id": ["obs-1"],
                "program_name": ["HALLMARK_HYPOXIA"],
                "raw_rank_evidence": [None],
                "signature_size_matched": [0],
            }
        ),
    )

    artifact = score_batch(
        expression_matrix={"obs-1": {"MKI67": 5.0}},
        signatures=(GeneSignature(name="HALLMARK_HYPOXIA", up_genes=("CA9", "VEGFA")),),
        scoring_contract_id="singscore_r_v1",
        target_definition_id="breast_visium_hallmarks_v1",
    )

    assert artifact.packets[0].status is ScoreStatus.DROPPED
    assert artifact.packets[0].failure_code is ScoreFailureCode.EMPTY_SIGNATURE_MATCH


def test_score_batch_fails_unsupported_directionality(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("R bridge should not run for unsupported signatures.")

    monkeypatch.setattr(SINGSCORE_MODULE, "run_r_script", fail_if_called)

    artifact = score_batch(
        expression_matrix={"obs-1": {"CA9": 5.0, "VEGFA": 4.0}},
        signatures=(
            GeneSignature(
                name="BIDIRECTIONAL",
                up_genes=("CA9",),
                down_genes=("VEGFA",),
            ),
        ),
        scoring_contract_id="singscore_r_v1",
        target_definition_id="breast_visium_hallmarks_v1",
    )

    assert artifact.packets[0].status is ScoreStatus.FAILED
    assert (
        artifact.packets[0].failure_code
        is ScoreFailureCode.UNSUPPORTED_DIRECTIONALITY
    )
