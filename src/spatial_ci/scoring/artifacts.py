"""Artifact schemas for the R-backed Spatial-CI scoring boundary."""

import json
import math
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable

import pyarrow as pa
import pyarrow.parquet as pq
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


def write_score_artifact(artifact: ScoreArtifact, path: Path) -> None:
    """Write a score artifact to Parquet with artifact metadata in schema metadata."""

    packet_rows = [packet.model_dump(mode="json") for packet in artifact.packets]
    table = pa.Table.from_pylist(packet_rows)
    artifact_metadata = artifact.model_dump(mode="json")
    artifact_metadata.pop("packets")
    schema_metadata = {
        **(table.schema.metadata or {}),
        b"spatial_ci_score_artifact": json.dumps(
            artifact_metadata, sort_keys=True
        ).encode("utf-8"),
    }
    pq.write_table(table.replace_schema_metadata(schema_metadata), path)


def read_score_artifact(path: Path) -> ScoreArtifact:
    """Read a score artifact from Parquet and reconstruct typed provenance and rows."""

    table = pq.read_table(path)
    schema_metadata = table.schema.metadata or {}
    encoded_metadata = schema_metadata.get(b"spatial_ci_score_artifact")
    if encoded_metadata is None:
        raise ValueError(
            "Parquet artifact is missing spatial_ci_score_artifact metadata."
        )

    artifact_metadata = json.loads(encoded_metadata.decode("utf-8"))
    packets = tuple(ScorePacket.model_validate(row) for row in table.to_pylist())
    return ScoreArtifact.model_validate({**artifact_metadata, "packets": packets})


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
    "read_score_artifact",
    "write_score_artifact",
]
