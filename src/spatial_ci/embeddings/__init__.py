"""Embedding artifact schemas."""

from spatial_ci.embeddings.artifacts import (
    EmbeddingArtifact,
    EmbeddingArtifactRow,
    read_embedding_artifact,
    write_embedding_artifact,
)

__all__ = [
    "EmbeddingArtifact",
    "EmbeddingArtifactRow",
    "read_embedding_artifact",
    "write_embedding_artifact",
]
