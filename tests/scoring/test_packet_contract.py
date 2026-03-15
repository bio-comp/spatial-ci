from pydantic import ValidationError

from spatial_ci.scoring.packet import (
    ScoreFailureCode,
    ScorePacket,
    SignatureCoverage,
    SignatureDirectionality,
)


def test_legacy_score_packet_rejects_missing_raw_evidence_without_failure_code(
) -> None:
    try:
        ScorePacket(
            sample_id="sample-1",
            signature_name="HALLMARK_HYPOXIA",
            scorer_name="dummy",
            signature_directionality=SignatureDirectionality.UP_ONLY,
            raw_rank_evidence=None,
            signature_coverage=SignatureCoverage(
                genes_total=2,
                genes_matched=2,
                coverage_fraction=1.0,
            ),
            failure_codes=(),
        )
    except ValidationError as exc:
        assert "failure_codes" in str(exc)
    else:
        raise AssertionError("Expected packet validation to fail.")


def test_legacy_score_packet_allows_missing_raw_evidence_when_failure_is_explicit(
) -> None:
    packet = ScorePacket(
        sample_id="sample-1",
        signature_name="HALLMARK_HYPOXIA",
        scorer_name="dummy",
        signature_directionality=SignatureDirectionality.UP_ONLY,
        raw_rank_evidence=None,
        signature_coverage=SignatureCoverage(
            genes_total=2,
            genes_matched=0,
            coverage_fraction=0.0,
        ),
        failure_codes=(ScoreFailureCode.MISSING_DATA,),
    )

    assert packet.failure_codes == (ScoreFailureCode.MISSING_DATA,)
