from collections.abc import Mapping

from spatial_ci.scoring.artifacts import (
    ScoreFailureCode,
    ScorePacket,
    ScorePacketAdapter,
    ScoreStatus,
)
from spatial_ci.signatures import GeneSignature


def test_score_packet_uses_observation_grain_and_status() -> None:
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
    assert packet.program_name == "HALLMARK_HYPOXIA"
    assert packet.status is ScoreStatus.OK


def test_score_packet_adapter_protocol_exposes_packet_output() -> None:
    class DummyAdapter:
        scorer_name = "dummy"

        def score(
            self,
            *,
            observation_id: str,
            expression_by_gene: Mapping[str, float],
            signature: GeneSignature,
        ) -> ScorePacket:
            return ScorePacket(
                observation_id=observation_id,
                sample_id=None,
                slide_id=None,
                program_name=signature.name,
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
            )

    adapter = DummyAdapter()

    assert isinstance(adapter, ScorePacketAdapter)
    packet = adapter.score(
        observation_id="obs-2",
        expression_by_gene={"CA9": 1.0, "VEGFA": 2.0},
        signature=GeneSignature(name="hypoxia", up_genes=("CA9", "VEGFA")),
    )
    assert packet.failure_code is ScoreFailureCode.EMPTY_SIGNATURE_MATCH
