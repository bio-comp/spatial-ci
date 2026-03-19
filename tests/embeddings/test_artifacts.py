from pathlib import Path

import pytest
from pydantic import ValidationError

from spatial_ci.embeddings.artifacts import (
    EmbeddingArtifact,
    EmbeddingArtifactRow,
    read_embedding_artifact,
    write_embedding_artifact,
)


def test_embedding_artifact_roundtrips_through_parquet(tmp_path: Path) -> None:
    artifact = EmbeddingArtifact(
        alignment_contract_id="alignment-v1",
        encoder_name="clip-vit-b32",
        encoder_version="1.0.0",
        source_embedding_artifact_path="embeddings/source.parquet",
        source_embedding_artifact_hash="a" * 64,
        n_rows=2,
        rows=(
            EmbeddingArtifactRow(
                observation_id="obs-1",
                sample_id="sample-1",
                embedding=(0.1, 0.2, 0.3),
            ),
            EmbeddingArtifactRow(
                observation_id="obs-2",
                sample_id="sample-2",
                embedding=(0.4, 0.5, 0.6),
            ),
        ),
    )
    path = tmp_path / "embeddings.parquet"

    write_embedding_artifact(artifact, path)
    observed = read_embedding_artifact(path)

    assert observed == artifact


def test_embedding_artifact_rejects_duplicate_observation_ids() -> None:
    row = EmbeddingArtifactRow(
        observation_id="obs-1",
        sample_id="sample-1",
        embedding=(0.1, 0.2, 0.3),
    )

    with pytest.raises(ValidationError, match="observation_id"):
        EmbeddingArtifact(
            alignment_contract_id="alignment-v1",
            encoder_name="clip-vit-b32",
            encoder_version="1.0.0",
            source_embedding_artifact_path=None,
            source_embedding_artifact_hash=None,
            n_rows=2,
            rows=(row, row),
        )


def test_embedding_artifact_rejects_inconsistent_embedding_dimensions() -> None:
    with pytest.raises(ValidationError, match="embedding"):
        EmbeddingArtifact(
            alignment_contract_id="alignment-v1",
            encoder_name="clip-vit-b32",
            encoder_version="1.0.0",
            source_embedding_artifact_path=None,
            source_embedding_artifact_hash=None,
            n_rows=2,
            rows=(
                EmbeddingArtifactRow(
                    observation_id="obs-1",
                    sample_id="sample-1",
                    embedding=(0.1, 0.2, 0.3),
                ),
                EmbeddingArtifactRow(
                    observation_id="obs-2",
                    sample_id="sample-2",
                    embedding=(0.4, 0.5),
                ),
            ),
        )


def test_embedding_artifact_requires_row_sample_id_and_metadata_fields() -> None:
    with pytest.raises(ValidationError, match="sample_id"):
        EmbeddingArtifactRow(
            observation_id="obs-1",
            embedding=(0.1, 0.2, 0.3),
        )

    with pytest.raises(ValidationError, match="encoder_name"):
        EmbeddingArtifact(
            alignment_contract_id="alignment-v1",
            encoder_version="1.0.0",
            source_embedding_artifact_path=None,
            source_embedding_artifact_hash=None,
            n_rows=0,
            rows=(),
        )
