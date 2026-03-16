import hashlib
from pathlib import Path

from spatial_ci.contracts.definitions import ArtifactProvenance
from spatial_ci.manifest.artifacts import ResolvedArtifact


def hash_file_sha256(path: Path) -> str:
    """Return a stable SHA256 hash for a file using chunked reads."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_artifact_provenance(
    resolved_artifact: ResolvedArtifact,
) -> ArtifactProvenance:
    """Hash one resolved artifact and return the manifest provenance record."""

    return ArtifactProvenance(
        path=resolved_artifact.path,
        hash_sha256=hash_file_sha256(resolved_artifact.path),
        artifact_type=resolved_artifact.artifact_type,
    )
