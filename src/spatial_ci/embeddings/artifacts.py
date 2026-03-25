"""Artifact schemas for embedding outputs."""

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator


class EmbeddingArtifactRow(BaseModel):
    """One embedding row at observation grain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    observation_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    embedding: tuple[FiniteFloat, ...] = Field(min_length=1)


class EmbeddingArtifact(BaseModel):
    """Artifact-level embedding provenance and rows."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    alignment_contract_id: str = Field(min_length=1)
    encoder_name: str = Field(min_length=1)
    encoder_version: str = Field(min_length=1)
    source_image_artifact_path: str | None = None
    source_image_artifact_hash: str | None = None
    n_rows: int = Field(ge=0)
    rows: tuple[EmbeddingArtifactRow, ...]

    @model_validator(mode="after")
    def _validate_rows(self) -> "EmbeddingArtifact":
        if self.source_image_artifact_path == "":
            raise ValueError("source_image_artifact_path must be non-empty when set")

        if self.source_image_artifact_hash == "":
            raise ValueError("source_image_artifact_hash must be non-empty when set")

        if (
            self.source_image_artifact_path is None
            and self.source_image_artifact_hash is not None
        ):
            raise ValueError(
                "source_image_artifact_path is required when "
                "source_image_artifact_hash is set"
            )

        if (
            self.source_image_artifact_path is not None
            and self.source_image_artifact_hash is None
        ):
            raise ValueError(
                "source_image_artifact_hash is required when "
                "source_image_artifact_path is set"
            )

        if self.n_rows != len(self.rows):
            raise ValueError("n_rows must match len(rows)")

        observation_ids = [row.observation_id for row in self.rows]
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("observation_id must be unique across rows")

        embedding_dimensions = {len(row.embedding) for row in self.rows}
        if len(embedding_dimensions) > 1:
            raise ValueError("embedding must have consistent dimensionality")

        sorted_rows = tuple(sorted(self.rows, key=lambda row: row.observation_id))
        object.__setattr__(self, "rows", sorted_rows)

        return self


def write_embedding_artifact(artifact: EmbeddingArtifact, path: Path) -> None:
    """Write an embedding artifact to Parquet with schema metadata."""

    sorted_rows = sorted(artifact.rows, key=lambda row: row.observation_id)
    row_table = pa.Table.from_pylist(
        [row.model_dump(mode="json") for row in sorted_rows]
    )
    artifact_metadata = artifact.model_dump(mode="json")
    artifact_metadata.pop("rows")
    schema_metadata = {
        **(row_table.schema.metadata or {}),
        b"spatial_ci_embedding_artifact": json.dumps(
            artifact_metadata, sort_keys=True
        ).encode("utf-8"),
    }
    pq.write_table(row_table.replace_schema_metadata(schema_metadata), path)


def read_embedding_artifact(path: Path) -> EmbeddingArtifact:
    """Read an embedding artifact from Parquet and reconstruct typed rows."""

    table = pq.read_table(path)
    schema_metadata = table.schema.metadata or {}
    encoded_metadata = schema_metadata.get(b"spatial_ci_embedding_artifact")
    if encoded_metadata is None:
        raise ValueError(
            "Parquet artifact is missing spatial_ci_embedding_artifact metadata."
        )

    artifact_metadata = json.loads(encoded_metadata.decode("utf-8"))
    rows = tuple(EmbeddingArtifactRow.model_validate(row) for row in table.to_pylist())
    return EmbeddingArtifact.model_validate({**artifact_metadata, "rows": rows})


__all__ = [
    "EmbeddingArtifact",
    "EmbeddingArtifactRow",
    "read_embedding_artifact",
    "write_embedding_artifact",
]
