"""Artifact schemas for the R-backed Spatial-CI scoring boundary."""

import math
from collections.abc import Mapping
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from spatial_ci.signatures import GeneSignature


class ScoreStatus(str, Enum):
    """High-level row status for score output."""

    OK = "ok"
    DROPPED = "dropped"
    FAILED = "failed"


class ScoreFailureCode(str, Enum):
    """Explicit failure or drop reasons for score rows."""

    LOW_SIGNATURE_COVERAGE = "low_signature_coverage"
    EMPTY_SIGNATURE_MATCH = "empty_signature_match"
    UNSUPPORTED_DIRECTIONALITY = "unsupported_directionality"
    R_SUBPROCESS_ERROR = "r_subprocess_error"
    INVALID_SCORER_OUTPUT = "invalid_scorer_output"
    INVALID_EXPRESSION_INPUT = "invalid_expression_input"


class SignatureDirection(str, Enum):
    """Declared directionality for a score artifact."""

    UP_ONLY = "up_only"
    UP_DOWN = "up_down"


class ScorePacket(BaseModel):
    """One score row at observation x program grain."""

    model_config = ConfigDict(frozen=True)

    observation_id: str = Field(min_length=1)
    sample_id: str | None = None
    slide_id: str | None = None
    program_name: str = Field(min_length=1)
    status: ScoreStatus
    raw_rank_evidence: float | None = None
    signature_size_declared: int = Field(ge=1)
    signature_size_matched: int = Field(ge=0)
    signature_coverage: float = Field(ge=0.0, le=1.0)
    dropped_by_missingness_rule: bool
    failure_code: ScoreFailureCode | None = None
    null_calibrated_score: float | None = None
    dropout_penalty: float | None = None
    spatial_consistency: float | None = None
    matched_gene_ids: tuple[str, ...] | None = None

    @model_validator(mode="after")
    def validate_consistency(self) -> "ScorePacket":
        if self.signature_size_matched > self.signature_size_declared:
            raise ValueError(
                "signature_size_matched must not exceed signature_size_declared."
            )

        expected_coverage = self.signature_size_matched / self.signature_size_declared
        if not math.isclose(
            self.signature_coverage,
            expected_coverage,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                "signature_coverage must match "
                "signature_size_matched / signature_size_declared."
            )

        if self.status is ScoreStatus.OK and self.failure_code is not None:
            raise ValueError("failure_code must be None when status is ok.")

        return self


class ScoreArtifact(BaseModel):
    """Artifact-level score collection plus provenance."""

    model_config = ConfigDict(frozen=True)

    target_definition_id: str = Field(min_length=1)
    scoring_contract_id: str = Field(min_length=1)
    signature_direction: SignatureDirection
    bridge_contract_version: str = Field(min_length=1)
    generated_at: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    r_version: str = Field(min_length=1)
    singscore_version: str = Field(min_length=1)
    renv_lock_hash: str = Field(min_length=1)
    scoring_script_path: str = Field(min_length=1)
    scoring_script_hash: str = Field(min_length=1)
    source_expression_artifact_hash: str | None = None
    source_manifest_id: str | None = None
    packets: tuple[ScorePacket, ...]


@runtime_checkable
class ScorePacketAdapter(Protocol):
    """Protocol for scorers that emit score packets."""

    scorer_name: str

    def score(
        self,
        *,
        observation_id: str,
        expression_by_gene: Mapping[str, float],
        signature: GeneSignature,
    ) -> ScorePacket: ...


__all__ = [
    "ScoreArtifact",
    "ScoreFailureCode",
    "ScorePacket",
    "ScorePacketAdapter",
    "ScoreStatus",
    "SignatureDirection",
]
