from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
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
        source_image_artifact_path="images/source.tiff",
        source_image_artifact_hash="a" * 64,
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


def test_embedding_artifact_canonicalizes_rows_by_observation_id() -> None:
    artifact = EmbeddingArtifact(
        alignment_contract_id="alignment-v1",
        encoder_name="clip-vit-b32",
        encoder_version="1.0.0",
        source_image_artifact_path=None,
        source_image_artifact_hash=None,
        n_rows=2,
        rows=(
            EmbeddingArtifactRow(
                observation_id="obs-2",
                sample_id="sample-2",
                embedding=(0.4, 0.5, 0.6),
            ),
            EmbeddingArtifactRow(
                observation_id="obs-1",
                sample_id="sample-1",
                embedding=(0.1, 0.2, 0.3),
            ),
        ),
    )

    assert tuple(row.observation_id for row in artifact.rows) == ("obs-1", "obs-2")


def test_embedding_artifact_writes_rows_in_observation_order(
    tmp_path: Path,
) -> None:
    artifact = EmbeddingArtifact(
        alignment_contract_id="alignment-v1",
        encoder_name="clip-vit-b32",
        encoder_version="1.0.0",
        source_image_artifact_path=None,
        source_image_artifact_hash=None,
        n_rows=2,
        rows=(
            EmbeddingArtifactRow(
                observation_id="obs-2",
                sample_id="sample-2",
                embedding=(0.4, 0.5, 0.6),
            ),
            EmbeddingArtifactRow(
                observation_id="obs-1",
                sample_id="sample-1",
                embedding=(0.1, 0.2, 0.3),
            ),
        ),
    )
    path = tmp_path / "embeddings.parquet"

    write_embedding_artifact(artifact, path)
    table = pq.read_table(path)

    assert [row["observation_id"] for row in table.to_pylist()] == [
        "obs-1",
        "obs-2",
    ]


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
            source_image_artifact_path=None,
            source_image_artifact_hash=None,
            n_rows=2,
            rows=(row, row),
        )


def test_embedding_artifact_rejects_inconsistent_embedding_dimensions() -> None:
    with pytest.raises(ValidationError, match="embedding"):
        EmbeddingArtifact(
            alignment_contract_id="alignment-v1",
            encoder_name="clip-vit-b32",
            encoder_version="1.0.0",
            source_image_artifact_path=None,
            source_image_artifact_hash=None,
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


def test_embedding_artifact_rejects_non_finite_embedding_values() -> None:
    with pytest.raises(ValidationError):
        EmbeddingArtifactRow(
            observation_id="obs-1",
            sample_id="sample-1",
            embedding=(float("nan"),),
        )

    with pytest.raises(ValidationError):
        EmbeddingArtifactRow(
            observation_id="obs-1",
            sample_id="sample-1",
            embedding=(float("inf"),),
        )


def test_embedding_artifact_requires_row_sample_id_and_metadata_fields() -> None:
    with pytest.raises(ValidationError, match="sample_id"):
        EmbeddingArtifactRow.model_validate(
            {"observation_id": "obs-1", "embedding": (0.1, 0.2, 0.3)}
        )

    with pytest.raises(ValidationError, match="encoder_name"):
        EmbeddingArtifact.model_validate(
            {
                "alignment_contract_id": "alignment-v1",
                "encoder_version": "1.0.0",
                "source_image_artifact_path": None,
                "source_image_artifact_hash": None,
                "n_rows": 0,
                "rows": (),
            }
        )


def test_embedding_artifact_requires_complete_non_empty_source_provenance() -> None:
    with pytest.raises(ValidationError, match="source_image_artifact_path"):
        EmbeddingArtifact(
            alignment_contract_id="alignment-v1",
            encoder_name="clip-vit-b32",
            encoder_version="1.0.0",
            source_image_artifact_path="",
            source_image_artifact_hash="a" * 64,
            n_rows=0,
            rows=(),
        )

    with pytest.raises(ValidationError, match="source_image_artifact_hash"):
        EmbeddingArtifact(
            alignment_contract_id="alignment-v1",
            encoder_name="clip-vit-b32",
            encoder_version="1.0.0",
            source_image_artifact_path="images/source.tiff",
            source_image_artifact_hash=None,
            n_rows=0,
            rows=(),
        )

    with pytest.raises(ValidationError, match="source_image_artifact_path"):
        EmbeddingArtifact(
            alignment_contract_id="alignment-v1",
            encoder_name="clip-vit-b32",
            encoder_version="1.0.0",
            source_image_artifact_path=None,
            source_image_artifact_hash="a" * 64,
            n_rows=0,
            rows=(),
        )


def test_embedding_artifact_rejects_unexpected_row_and_metadata_keys() -> None:
    with pytest.raises(ValidationError, match="extra"):
        EmbeddingArtifactRow.model_validate(
            {
                "observation_id": "obs-1",
                "sample_id": "sample-1",
                "embedding": (0.1, 0.2, 0.3),
                "unexpected": "value",
            }
        )

    with pytest.raises(ValidationError, match="extra"):
        EmbeddingArtifact.model_validate(
            {
                "alignment_contract_id": "alignment-v1",
                "encoder_name": "clip-vit-b32",
                "encoder_version": "1.0.0",
                "source_image_artifact_path": None,
                "source_image_artifact_hash": None,
                "n_rows": 0,
                "rows": (),
                "unexpected": "value",
            }
        )


def test_embedding_artifact_read_rejects_missing_schema_metadata(
    tmp_path: Path,
) -> None:
    path = tmp_path / "embeddings.parquet"
    pq.write_table(pa.table({"observation_id": ["obs-1"]}), path)

    with pytest.raises(ValueError, match="spatial_ci_embedding_artifact"):
        read_embedding_artifact(path)
