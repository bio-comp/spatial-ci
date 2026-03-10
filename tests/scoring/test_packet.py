from collections.abc import Mapping

import pytest
from pydantic import ValidationError

from spatial_ci.scoring import (
    ScoreFailureCode,
    ScorePacket,
    ScorePacketAdapter,
    SignatureCoverage,
    SignatureDirectionality,
    UncertaintyFlag,
)
from spatial_ci.signatures import GeneSignature


def test_score_packet_supports_explicit_failure_codes_and_optional_fields() -> None:
    packet = ScorePacket(
        sample_id="spot_001",
        signature_name="HALLMARK_HYPOXIA",
        scorer_name="singscore",
        signature_directionality=SignatureDirectionality.UP_ONLY,
        raw_rank_evidence=0.42,
        signature_coverage=SignatureCoverage(
            genes_total=10,
            genes_matched=8,
            coverage_fraction=0.8,
        ),
        dropout_penalty=None,
        null_calibrated_score=None,
        spatial_consistency=None,
        uncertainty_flag=UncertaintyFlag.HIGH,
        failure_codes=(
            ScoreFailureCode.MISSING_DATA,
            ScoreFailureCode.NULL_CALIBRATION_MISSING,
        ),
    )

    assert packet.sample_id == "spot_001"
    assert packet.signature_coverage.coverage_fraction == pytest.approx(0.8)
    assert packet.failure_codes == (
        ScoreFailureCode.MISSING_DATA,
        ScoreFailureCode.NULL_CALIBRATION_MISSING,
    )


def test_signature_coverage_rejects_fraction_mismatch() -> None:
    with pytest.raises(ValidationError, match="coverage_fraction"):
        SignatureCoverage(
            genes_total=10,
            genes_matched=8,
            coverage_fraction=0.5,
        )


def test_score_packet_adapter_protocol_exposes_packet_output() -> None:
    class DummyAdapter:
        scorer_name = "dummy"

        def score(
            self,
            *,
            sample_id: str,
            expression_by_gene: Mapping[str, float],
            signature: GeneSignature,
        ) -> ScorePacket:
            return ScorePacket(
                sample_id=sample_id,
                signature_name=signature.name,
                scorer_name=self.scorer_name,
                signature_directionality=SignatureDirectionality.UP_ONLY,
                raw_rank_evidence=0.1,
                signature_coverage=SignatureCoverage(
                    genes_total=2,
                    genes_matched=2,
                    coverage_fraction=1.0,
                ),
                dropout_penalty=0.0,
                null_calibrated_score=None,
                spatial_consistency=None,
                uncertainty_flag=UncertaintyFlag.NONE,
                failure_codes=(),
            )

    adapter = DummyAdapter()

    assert isinstance(adapter, ScorePacketAdapter)
    packet = adapter.score(
        sample_id="spot_002",
        expression_by_gene={"CA9": 1.0, "VEGFA": 2.0},
        signature=GeneSignature(name="hypoxia", up_genes=("CA9", "VEGFA")),
    )
    assert packet.scorer_name == "dummy"
