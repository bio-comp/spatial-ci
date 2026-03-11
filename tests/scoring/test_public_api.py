import importlib

import pytest

from spatial_ci.scoring import (
    CalibrationStatus,
    ReferencePopulation,
    ReferencePopulationKind,
    robust_calibrate_scores,
    score_batch,
    score_one,
)
from spatial_ci.signatures import GeneSignature

SCORING_MODULE = importlib.import_module("spatial_ci.scoring")


def test_scoring_public_api_is_available() -> None:
    signature = GeneSignature(name="hypoxia", up_genes=("CA9", "VEGFA"))

    assert signature.up_genes == ("CA9", "VEGFA")
    assert CalibrationStatus.OK.value == "ok"
    assert ReferencePopulationKind.TRAINING.value == "training"
    assert ReferencePopulation(
        label="train",
        kind=ReferencePopulationKind.TRAINING,
        sample_ids=("spot_1", "spot_2", "spot_3"),
    ).sample_ids == ("spot_1", "spot_2", "spot_3")
    assert callable(score_batch)
    assert callable(score_one)
    assert callable(robust_calibrate_scores)
    assert "MissingGenePolicy" not in SCORING_MODULE.__all__
    assert "TiePolicy" not in SCORING_MODULE.__all__
    assert "ScoreResult" not in SCORING_MODULE.__all__
    assert "singscore" not in SCORING_MODULE.__all__


def test_gene_signature_rejects_duplicate_genes() -> None:
    with pytest.raises(ValueError, match="duplicate genes"):
        GeneSignature(name="bad", up_genes=("CA9", "CA9"))


def test_gene_signature_rejects_overlap_between_directions() -> None:
    with pytest.raises(ValueError, match="must be disjoint"):
        GeneSignature(name="bad", up_genes=("CA9",), down_genes=("CA9",))
