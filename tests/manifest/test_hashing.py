import hashlib
from pathlib import Path

from spatial_ci.manifest.artifacts import ResolvedArtifact
from spatial_ci.manifest.hashing import build_artifact_provenance, hash_file_sha256


def test_hash_file_sha256_is_stable_for_fixture_file() -> None:
    path = Path("tests/fixtures/manifest/pass2/sample-root/spot-1/image.tiff")
    expected = hashlib.sha256(path.read_bytes()).hexdigest()

    assert hash_file_sha256(path) == expected


def test_build_artifact_provenance_hashes_resolved_artifact() -> None:
    path = Path("tests/fixtures/manifest/pass2/sample-root/spot-1/image.tiff")

    provenance = build_artifact_provenance(
        ResolvedArtifact(
            artifact_type="image",
            path=path,
        )
    )

    assert provenance.path == path
    assert provenance.artifact_type == "image"
    assert provenance.hash_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
