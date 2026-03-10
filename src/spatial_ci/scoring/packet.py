"""Packet-style scoring contracts for audit-friendly scorer output."""

import math
from collections.abc import Mapping
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from spatial_ci.signatures import GeneSignature


class SignatureDirectionality(str, Enum):
    """Explicit directionality for a scored signature packet."""

    UP_ONLY = "up_only"
    UP_DOWN = "up_down"


class UncertaintyFlag(str, Enum):
    """High-level uncertainty flag for human review."""

    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ScoreFailureCode(str, Enum):
    """Explicit scorer failure or caveat codes."""

    MISSING_DATA = "missing_data"
    LOW_COVERAGE = "low_coverage"
    NULL_CALIBRATION_MISSING = "null_calibration_missing"
    DEGENERATE_REFERENCE_DISTRIBUTION = "degenerate_reference_distribution"
    DIRECTIONALITY_UNSUPPORTED = "directionality_unsupported"
    SPATIAL_CONTEXT_MISSING = "spatial_context_missing"


class SignatureCoverage(BaseModel):
    """Coverage accounting for a scored signature."""

    model_config = ConfigDict(frozen=True)

    genes_total: int = Field(ge=1)
    genes_matched: int = Field(ge=0)
    coverage_fraction: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_coverage_fraction(self) -> "SignatureCoverage":
        if self.genes_matched > self.genes_total:
            raise ValueError("genes_matched must not exceed genes_total.")

        expected_fraction = self.genes_matched / self.genes_total
        if not math.isclose(
            self.coverage_fraction,
            expected_fraction,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                "coverage_fraction must match genes_matched / genes_total."
            )

        return self


class ScorePacket(BaseModel):
    """Decision-oriented packet emitted by scorer adapters."""

    model_config = ConfigDict(frozen=True)

    sample_id: str
    signature_name: str
    scorer_name: str
    signature_directionality: SignatureDirectionality
    raw_rank_evidence: float | None = None
    signature_coverage: SignatureCoverage
    dropout_penalty: float | None = None
    null_calibrated_score: float | None = None
    spatial_consistency: float | None = None
    uncertainty_flag: UncertaintyFlag = UncertaintyFlag.NONE
    failure_codes: tuple[ScoreFailureCode, ...] = ()
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


@runtime_checkable
class ScorePacketAdapter(Protocol):
    """Protocol for scorers that emit packet-shaped outputs."""

    scorer_name: str

    def score(
        self,
        *,
        sample_id: str,
        expression_by_gene: Mapping[str, float],
        signature: GeneSignature,
    ) -> ScorePacket: ...
