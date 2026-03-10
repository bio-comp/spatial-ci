import pytest

from spatial_ci.scoring import (
    CalibrationStatus,
    MissingGenePolicy,
    ReferencePopulation,
    ReferencePopulationKind,
    TiePolicy,
    robust_calibrate_scores,
    singscore,
)
from spatial_ci.signatures import GeneSignature


def test_scoring_public_api_is_available() -> None:
    signature = GeneSignature(name="hypoxia", up_genes=("CA9", "VEGFA"))

    assert signature.up_genes == ("CA9", "VEGFA")
    assert MissingGenePolicy.INTERSECT.value == "intersect"
    assert TiePolicy.AVERAGE.value == "average"
    assert CalibrationStatus.OK.value == "ok"
    assert ReferencePopulationKind.TRAINING.value == "training"
    assert ReferencePopulation(
        label="train",
        kind=ReferencePopulationKind.TRAINING,
        sample_ids=("spot_1", "spot_2", "spot_3"),
    ).sample_ids == ("spot_1", "spot_2", "spot_3")
    assert callable(singscore)
    assert callable(robust_calibrate_scores)


def test_gene_signature_rejects_duplicate_genes() -> None:
    with pytest.raises(ValueError, match="duplicate genes"):
        GeneSignature(name="bad", up_genes=("CA9", "CA9"))


def test_gene_signature_rejects_overlap_between_directions() -> None:
    with pytest.raises(ValueError, match="must be disjoint"):
        GeneSignature(name="bad", up_genes=("CA9",), down_genes=("CA9",))


def test_singscore_raises_until_parity_contract_exists() -> None:
    signature = GeneSignature(name="hypoxia", up_genes=("CA9", "VEGFA"))

    with pytest.raises(NotImplementedError, match="internal-first"):
        singscore({"CA9": 1.0, "VEGFA": 2.0}, signature)
